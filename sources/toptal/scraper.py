import pandas as pd
from bs4 import BeautifulSoup
import time
import logging
from sources.validators import validate_and_clean_job
from sources.browser_utils import fetch_html

logger = logging.getLogger("JobScraper.Toptal")

BASE_URL = "https://www.toptal.com"

def fetch_toptal_jobs():
    """
    Scrapes Toptal job listings via JavaScript rendering (SPA).
    Note: Toptal is a freelancer platform and does not have public job listings.
    The /jobs URL returns 404. This scraper returns empty results.
    """
    # Toptal /jobs returns 404 - it's a freelancer platform, not a job board
    logger.debug("Toptal is a freelancer platform and does not have public job listings")
    return pd.DataFrame()

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
                job_url = BASE_URL + job_url

            company_el = (
                card.select_one("span[class*='company']") or
                card.select_one("div[class*='company']")
            )

            # Toptal jobs are typically remote
            is_remote = True  # Toptal focuses on remote work

            job_data = {
                "site": "toptal",
                "title": title,
                "company": company_el.get_text(strip=True) if company_el else None,
                "location": "Remote",
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
