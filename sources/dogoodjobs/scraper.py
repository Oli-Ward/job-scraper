import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import logging
from sources.validators import validate_and_clean_job

logger = logging.getLogger("JobScraper.DoGoodJobs")

BASE_URL = "https://jobs.dogoodjobs.co.nz"

def fetch_dogoodjobs_jobs():
    """
    Scrapes Do Good Jobs job listings via HTML parsing.
    """
    url = f"{BASE_URL}/jobs/"

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
        
        # Find job articles - they have class listing-item__jobs
        job_articles = soup.select("article.listing-item__jobs")
        
        for article in job_articles:
            try:
                # Title is in div.media-heading.listing-item__title > a
                title_el = article.select_one("div.listing-item__title a, .media-heading a")
                if not title_el:
                    continue
                
                title = title_el.get_text(strip=True)
                job_url = title_el.get("href", "")
                if not job_url.startswith("http"):
                    job_url = BASE_URL + job_url if job_url.startswith("/") else BASE_URL + "/" + job_url
                
                # Organization/company - try image alt or other elements
                company_el = (
                    article.select_one("img[alt]") or
                    article.select_one("span[class*='organisation'], div[class*='organisation']") or
                    article.select_one("span[class*='company'], div[class*='company']")
                )
                company = None
                if company_el:
                    if company_el.name == "img":
                        company = company_el.get("alt", "").strip()
                    else:
                        company = company_el.get_text(strip=True)
                
                # Location - in listing-item__info
                location_el = article.select_one("span[class*='location'], div[class*='location'], .listing-item__info--location")
                location = "New Zealand"
                if location_el:
                    location_text = location_el.get_text(strip=True)
                    # Extract location from text (often has format like "Wellington, New Zealand")
                    if location_text:
                        location = location_text.split(",")[0].strip() if "," in location_text else location_text
                
                # Check for remote
                card_text = article.get_text().lower()
                is_remote = any(
                    keyword in card_text
                    for keyword in ["remote", "work from home", "wfh", "hybrid"]
                )
                
                # Date posted
                date_el = article.select_one(".listing-item__date")
                date_posted = date_el.get_text(strip=True) if date_el else None

                job_data = {
                    "site": "dogoodjobs",
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
                logger.debug(f"Error parsing job article: {e}")
                continue

    except requests.RequestException as e:
        logger.warning(f"Error fetching jobs: {e}")
    except Exception as e:
        logger.warning(f"Error parsing jobs page: {e}")

    time.sleep(1)
    return pd.DataFrame(jobs)
