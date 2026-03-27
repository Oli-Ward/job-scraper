import pandas as pd
from bs4 import BeautifulSoup
import time
import logging
from sources.validators import validate_and_clean_job
from sources.browser_utils import fetch_html

logger = logging.getLogger("JobScraper.Turing")

BASE_URL = "https://www.turing.com"

def fetch_turing_jobs():
    """
    Scrapes Turing job listings via JavaScript rendering (SPA).
    Note: Turing is blocked by Incapsula bot protection and cannot be scraped.
    This scraper returns empty results.
    """
    # Turing is blocked by Incapsula bot protection
    logger.debug("Turing is blocked by bot protection (Incapsula) and cannot be scraped")
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

            # Turing jobs are remote
            is_remote = True

            job_data = {
                "site": "turing",
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
