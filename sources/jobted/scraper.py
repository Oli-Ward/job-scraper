import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import logging
from sources.validators import validate_and_clean_job

logger = logging.getLogger("JobScraper.Jobted")

BASE_URL = "https://www.jobted.co.nz/software-engineer-jobs"

def fetch_jobted_jobs():
    """
    Scrapes Jobted NZ job listings via HTML parsing.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-NZ,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    # Try with longer timeout and retry logic
    max_retries = 2
    timeout = 30  # Increased from 15 to 30 seconds
    
    for attempt in range(max_retries):
        try:
            res = requests.get(BASE_URL, headers=headers, timeout=timeout)
            res.raise_for_status()
            break  # Success, exit retry loop
        except requests.Timeout as e:
            if attempt < max_retries - 1:
                logger.debug(f"Timeout on attempt {attempt + 1}, retrying...")
                time.sleep(2)  # Wait before retry
                continue
            else:
                logger.warning(f"Error fetching jobs: Read timeout after {max_retries} attempts")
                return pd.DataFrame()
        except requests.RequestException as e:
            logger.warning(f"Error fetching jobs: {e}")
            return pd.DataFrame()

    soup = BeautifulSoup(res.text, "html.parser")
    jobs = []

    job_cards = (
        soup.select("div[class*='job']") or
        soup.select("article[class*='job']") or
        soup.select("li[class*='job']")
    )

    for card in job_cards:
        try:
            title_el = (
                card.select_one("a[href*='/job/']") or
                card.select_one("h2 a") or
                card.select_one("h3 a") or
                card.select_one("a[class*='title']")
            )
            
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            job_url = title_el.get("href", "")
            if job_url and not job_url.startswith("http"):
                job_url = "https://www.jobted.co.nz" + job_url

            company_el = (
                card.select_one("span[class*='company']") or
                card.select_one("div[class*='company']")
            )

            location_el = (
                card.select_one("span[class*='location']") or
                card.select_one("div[class*='location']")
            )

            card_text = card.get_text().lower()
            is_remote = any(
                keyword in card_text
                for keyword in ["remote", "work from home", "wfh"]
            )

            job_data = {
                "site": "jobted",
                "title": title,
                "company": company_el.get_text(strip=True) if company_el else None,
                "location": location_el.get_text(strip=True) if location_el else "New Zealand",
                "is_remote": is_remote,
                "job_url": job_url,
                "date_posted": None,
                "description": None,
            }

            # Validate and clean job data
            validated_job = validate_and_clean_job(job_data)
            if validated_job:
                jobs.append(validated_job)

        except Exception as e:
            logger.debug(f"Error parsing job card: {e}")
            continue

    time.sleep(1)
    return pd.DataFrame(jobs)
