import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import logging
from sources.validators import validate_and_clean_job

logger = logging.getLogger("JobScraper.RwaJobs")

BASE_URL = "https://www.rwa.co.nz"

def fetch_rwajobs_jobs():
    """
    Scrapes RWA Jobs listings via HTML parsing.
    """
    url = f"{BASE_URL}/our-jobs"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-NZ,en;q=0.9",
    }

    jobs = []

    try:
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Find job card wrappers - they have class job-card-wrapper
        job_cards = soup.select("div.job-card-wrapper")
        
        for card in job_cards:
            try:
                # Find the link - it's usually the main link in the card
                link_el = card.select_one("a[href*='/our-jobs/']")
                if not link_el:
                    continue
                
                job_url = link_el.get("href", "")
                if not job_url.startswith("http"):
                    job_url = BASE_URL + job_url if job_url.startswith("/") else BASE_URL + "/" + job_url
                
                # Title is in div.job-title
                title_el = card.select_one("div.job-title, .job-title")
                if not title_el:
                    # Fallback: use link text
                    title = link_el.get_text(strip=True)
                else:
                    title = title_el.get_text(strip=True)
                
                # Location and other info in div.job-timer
                timer_el = card.select_one("div.job-timer")
                location = "New Zealand"
                if timer_el:
                    timer_text = timer_el.get_text(strip=True)
                    # Parse location from timer text (format: "Category | Type | Location | Posted date")
                    parts = [p.strip() for p in timer_text.split("|")]
                    # Location is usually the third part
                    if len(parts) >= 3:
                        location = parts[2]
                
                # Department/category in div.job-department
                department_el = card.select_one("div.job-department")
                company = department_el.get_text(strip=True) if department_el else None
                
                # Check for remote
                card_text = card.get_text().lower()
                is_remote = any(
                    keyword in card_text
                    for keyword in ["remote", "work from home", "wfh", "hybrid"]
                )
                
                # Date posted - try to extract from timer text
                date_posted = None
                if timer_el:
                    timer_text = timer_el.get_text(strip=True)
                    if "Posted" in timer_text:
                        # Extract date part
                        date_part = timer_text.split("Posted")[-1].strip()
                        date_posted = date_part if date_part else None

                job_data = {
                    "site": "rwajobs",
                    "title": title,
                    "company": company,
                    "location": location,
                    "is_remote": is_remote,
                    "job_url": job_url,
                    "date_posted": date_posted,
                    "description": None,
                }

                # Validate and clean job data
                validated_job = validate_and_clean_job(job_data)
                if validated_job:
                    jobs.append(validated_job)

            except Exception as e:
                logger.debug(f"Error parsing job card: {e}")
                continue

    except requests.RequestException as e:
        logger.warning(f"Error fetching jobs: {e}")
    except Exception as e:
        logger.warning(f"Error parsing jobs page: {e}")

    time.sleep(1)
    return pd.DataFrame(jobs)
