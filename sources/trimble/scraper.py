import pandas as pd
from bs4 import BeautifulSoup
import time
import logging
from sources.validators import validate_and_clean_job
from sources.browser_utils import fetch_html

logger = logging.getLogger("JobScraper.Trimble")

BASE_URL = "https://trimble.eightfold.ai"

def fetch_trimble_jobs():
    """
    Scrapes Trimble job listings via JavaScript rendering (Eightfold.ai platform).
    """
    # Eightfold.ai platform requires JavaScript rendering
    # Use "load" instead of "networkidle" to avoid timeout
    html = fetch_html(
        BASE_URL,
        use_js=True,
        wait_selector="div[class*='job'], div[data-job-id], [data-eightfold-job]",
        timeout=60,  # 60 seconds (converted to milliseconds by fetch_html)
        wait_until="load"  # Wait for page load instead of networkidle
    )
    
    if not html:
        return pd.DataFrame()
    
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    # Eightfold.ai job links - look for links with /careers/job/ pattern
    job_links = soup.select("a[href*='/careers/job/']")
    
    if not job_links:
        # Fallback: try to find job cards by class
        job_cards = (
            soup.select("div[class*='cardcontainer']") or
            soup.select("div[class*='position-title']") or
            soup.select("div[class*='card-']")
        )
        
        if job_cards:
            # Extract links from cards
            for card in job_cards:
                link = card.select_one("a[href*='/careers/job/']")
                if link:
                    job_links.append(link)
    
    if not job_links:
        logger.debug("No job links found - page may not have loaded properly")
        return pd.DataFrame()

    for link in job_links:
        try:
            job_url = link.get("href", "")
            if not job_url:
                continue
            
            if not job_url.startswith("http"):
                job_url = BASE_URL + job_url
            
            # Get title from link text or nearby element
            title = link.get_text(strip=True)
            if not title:
                # Try to find title in parent or nearby elements
                parent = link.find_parent()
                if parent:
                    title_el = parent.select_one("[class*='position-title'], [class*='title']")
                    if title_el:
                        title = title_el.get_text(strip=True)
            
            if not title:
                continue
            
            # Find location - look in parent or nearby elements
            parent = link.find_parent()
            location = "New Zealand"
            if parent:
                location_el = parent.select_one("[class*='position-location'], [class*='location']")
                if location_el:
                    location = location_el.get_text(strip=True)
            
            card_text = (link.get_text() + " " + (parent.get_text() if parent else "")).lower()
            is_remote = any(
                keyword in card_text
                for keyword in ["remote", "work from home", "wfh"]
            )

            job_data = {
                "site": "trimble",
                "title": title,
                "company": "Trimble",
                "location": location if location else "New Zealand",
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
            logger.debug(f"Error parsing job link: {e}")
            continue

    time.sleep(1)
    return pd.DataFrame(jobs)
