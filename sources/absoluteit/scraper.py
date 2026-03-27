import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import time
import logging
from sources.validators import validate_and_clean_job
from sources.browser_utils import fetch_html

logger = logging.getLogger("JobScraper.AbsoluteIt")

BASE_URL = "https://absoluteit.co.nz"

def fetch_absoluteit_jobs():
    """
    Scrapes Absolute IT job listings via JavaScript rendering (has iframe).
    """
    # Try the main jobs page - may require JavaScript rendering
    url = f"{BASE_URL}/jobs"
    
    # Use "load" instead of "networkidle" to avoid timeout
    html = fetch_html(
        url,
        use_js=True,
        wait_selector="div[class*='job'], article[class*='job'], li[class*='job'], div[class*='vacancy']",
        timeout=60,  # 60 seconds (converted to milliseconds by fetch_html)
        wait_until="load"  # Wait for page load instead of networkidle
    )
    
    if not html:
        return pd.DataFrame()
    
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    
    # Absolute IT uses div.card.card-job for job cards
    job_cards = soup.select("div.card.card-job")
    
    if not job_cards:
        logger.debug("No job cards found - page may not have loaded properly")
        return pd.DataFrame()

    for card in job_cards:
        try:
            # Title is in h3.heading.card-job__title (not a link)
            title_el = card.select_one("h3.card-job__title")
            if not title_el:
                # Fallback selectors
                title_el = card.select_one("h2") or card.select_one("h3")
            
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            
            # Job URL is in the "Read more" button
            job_url_el = card.select_one("a.btn.btn-outline-primary")
            if not job_url_el:
                # Fallback to any link with /it-job/ in href
                job_url_el = card.select_one("a[href*='/it-job/']")
            
            job_url = ""
            if job_url_el:
                job_url = job_url_el.get("href", "")
            if job_url and not job_url.startswith("http"):
                job_url = BASE_URL + job_url

            # Company name - may not be in card structure, set to None
            company_el = None

            # Location is in div.card-job__location
            location_el = card.select_one("div.card-job__location a")
            if not location_el:
                location_el = card.select_one("div[class*='location']")

            card_text = card.get_text().lower()
            is_remote = any(
                keyword in card_text
                for keyword in ["remote", "work from home", "wfh"]
            )

            job_data = {
                "site": "absoluteit",
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
