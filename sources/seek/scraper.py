import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import time
import logging
from sources.validators import validate_and_clean_job

logger = logging.getLogger("JobScraper.Seek")

BASE_URL = "https://www.seek.co.nz/jobs"
KEYWORDS = "react typescript javascript node"

def fetch_seek_jobs():
    """
    Scrapes Seek NZ job listings via HTML parsing.
    Switch to api.py once API credentials are approved.
    """
    params = {
        "keywords": KEYWORDS,
        "where": "New Zealand",
        "classification": "6281",  # ICT
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-NZ,en;q=0.9",
    }

    url = f"{BASE_URL}?{urlencode(params)}"
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Error fetching jobs: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(res.text, "html.parser")
    jobs = []

    # Seek uses this structure as of Jan 2025
    job_cards = soup.select("article[data-card-type='JobCard']")
    
    if not job_cards:
        # Fallback selector if structure changed
        job_cards = soup.select("article[data-automation='normalJob']")

    for card in job_cards:
        try:
            title_el = card.select_one("a[data-automation='jobTitle']")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            job_url = title_el.get("href", "")
            if job_url and not job_url.startswith("http"):
                job_url = "https://www.seek.co.nz" + job_url

            company_el = card.select_one("[data-automation='jobCompany']")

            # Get all location elements and combine them
            location_parts = card.select("[data-automation='jobLocation']")
            location = ", ".join([loc.get_text(strip=True) for loc in location_parts]) if location_parts else None

            # Check for remote indicators
            is_remote = any(
                keyword in title.lower() 
                for keyword in ["remote", "work from home", "wfh"]
            )

            job_data = {
                "site": "seek",
                "title": title,
                "company": company_el.get_text(strip=True) if company_el else None,
                "location": location,
                "is_remote": is_remote,
                "job_url": job_url,
                "date_posted": None,  # Not easily available without API
                "description": None,  # Would require fetching each job page
            }
            
            # Validate and clean job data
            validated_job = validate_and_clean_job(job_data)
            if validated_job:
                jobs.append(validated_job)

        except Exception as e:
            logger.debug(f"Error parsing job card: {e}")
            continue

    # Rate limiting courtesy
    time.sleep(1)

    return pd.DataFrame(jobs)