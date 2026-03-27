import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import time
import logging
from sources.validators import validate_and_clean_job

logger = logging.getLogger("JobScraper.RobertHalf")

BASE_URL = "https://www.roberthalf.com/nz/en/jobs"

def fetch_roberthalf_jobs():
    """
    Scrapes Robert Half NZ job listings via HTML parsing.
    """
    params = {
        "keywords": "react typescript javascript node software",
        "location": "New Zealand",
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
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

    # Try multiple selectors for job cards
    job_cards = (
        soup.select("div[class*='job']") or
        soup.select("article[class*='job']") or
        soup.select("li[class*='job']") or
        soup.select("div[data-job-id]")
    )

    for card in job_cards:
        try:
            # Try multiple selectors for title
            title_el = (
                card.select_one("a[href*='/job/']") or
                card.select_one("h2 a") or
                card.select_one("h3 a") or
                card.select_one("a[class*='title']") or
                card.select_one("a[class*='job-title']")
            )
            
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            job_url = title_el.get("href", "")
            if job_url and not job_url.startswith("http"):
                job_url = "https://www.roberthalf.com" + job_url

            # Try multiple selectors for company (may be Robert Half itself)
            company_el = (
                card.select_one("span[class*='company']") or
                card.select_one("div[class*='company']") or
                card.select_one("p[class*='company']")
            )

            # Try multiple selectors for location
            location_el = (
                card.select_one("span[class*='location']") or
                card.select_one("div[class*='location']") or
                card.select_one("p[class*='location']") or
                card.select_one("[data-location]")
            )

            # Check for remote indicators
            card_text = card.get_text().lower()
            is_remote = any(
                keyword in card_text
                for keyword in ["remote", "work from home", "wfh", "flexible location"]
            )

            job_data = {
                "site": "roberthalf",
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

    # Rate limiting courtesy
    time.sleep(1)

    return pd.DataFrame(jobs)
