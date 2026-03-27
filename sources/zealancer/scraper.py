import pandas as pd
from bs4 import BeautifulSoup
import time
import logging
from sources.validators import validate_and_clean_job
from sources.browser_utils import fetch_html

logger = logging.getLogger("JobScraper.Zealancer")

BASE_URL = "https://www.zealancer.nz"

def fetch_zealancer_jobs():
    """
    Scrapes Zealancer.nz job listings via JavaScript rendering (SPA).
    Note: Zealancer may not have public job listings on their website.
    """
    # Try the main jobs page
    url = f"{BASE_URL}/jobs"
    
    html = fetch_html(
        url,
        use_js=True,
        wait_selector=None,
        timeout=30,
        wait_until="load"
    )
    
    if not html:
        return pd.DataFrame()
    
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    
    # Check if page has job-related content
    text = soup.get_text()
    if not any(keyword in text.lower() for keyword in ['job', 'position', 'vacancy', 'role', 'opening']):
        logger.debug("No job-related content found - Zealancer may not have public job board")
        return pd.DataFrame()
    
    job_cards = (
        soup.select("div[class*='job']") or
        soup.select("article[class*='job']") or
        soup.select("li[class*='job']") or
        soup.select("div[class*='position']") or
        soup.select("div[class*='vacancy']") or
        soup.select("div[class*='opening']")
    )
    
    if not job_cards:
        logger.debug("No job cards found - Zealancer may not have public job board")
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
                "site": "zealancer",
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
