import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import time
import logging
from sources.validators import validate_and_clean_job
from sources.browser_utils import fetch_html

logger = logging.getLogger("JobScraper.JobsGovernment")

BASE_URL = "https://jobs.govt.nz"

def fetch_jobsgovernment_jobs():
    """
    Scrapes Jobs Government (jobs.govt.nz) listings via JavaScript rendering.
    The site may require JavaScript to load search results properly.
    """
    # Use the main search page with keywords
    params = {
        "keywords": "software",
    }
    
    url = f"{BASE_URL}?{urlencode(params)}"
    
    # Try JavaScript rendering as the site may require it
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

    # Jobs Government may use table structure or divs
    job_cards = (
        soup.select("table tr[class*='job']") or
        soup.select("table tr") or
        soup.select("div[class*='job']") or
        soup.select("article[class*='job']") or
        soup.select("li[class*='job']") or
        soup.select("div[class*='vacancy']") or
        soup.select("div[class*='result']")
    )
    
    # Filter table rows to only those that look like job listings
    if job_cards and job_cards[0].name == 'tr':
        # Filter out header rows and non-job rows
        job_cards = [row for row in job_cards if len(row.select('a[href*="jobtools"]')) > 0]

    for card in job_cards:
        try:
            # For table rows, look for links in cells
            title_el = (
                card.select_one("a[href*='jobtools']") or
                card.select_one("a[href*='/job/']") or
                card.select_one("a[href*='/vacancy/']") or
                card.select_one("h2 a") or
                card.select_one("h3 a") or
                card.select_one("a[class*='title']") or
                card.select_one("td a")
            )
            
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title:
                continue
                
            job_url = title_el.get("href", "")
            if job_url and not job_url.startswith("http"):
                job_url = BASE_URL + job_url

            company_el = (
                card.select_one("span[class*='company']") or
                card.select_one("div[class*='company']") or
                card.select_one("span[class*='department']")
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
                "site": "jobsgovernment",
                "title": title,
                "company": company_el.get_text(strip=True) if company_el else "New Zealand Government",
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
