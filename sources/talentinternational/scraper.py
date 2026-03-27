import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import time
import logging
from sources.validators import validate_and_clean_job
from sources.browser_utils import fetch_html

logger = logging.getLogger("JobScraper.TalentInternational")

BASE_URL = "https://www.talentinternational.com"

def fetch_talentinternational_jobs():
    """
    Scrapes Talent International job listings via JavaScript rendering.
    Jobs are loaded dynamically in li.job-card elements.
    """
    params = {
        "keywords": "software",
    }

    url = f"{BASE_URL}/search-jobs/?{urlencode(params)}"

    # Use JavaScript rendering as jobs are loaded dynamically
    html = fetch_html(
        url,
        use_js=True,
        wait_selector="li[class*='job-card']",
        timeout=60,
        wait_until="load"
    )
    
    if not html:
        return pd.DataFrame()
    
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    # Job cards are in li elements with class "job-card"
    job_cards = soup.select("li[class*='job-card']")
    
    if not job_cards:
        logger.debug("No job cards found - page may not have loaded properly")
        return pd.DataFrame()

    for card in job_cards:
        try:
            # Title is in h1 inside job-card__header
            header = card.select_one("header[class*='job-card__header']")
            if header:
                title_el = header.select_one("h1, h2, h3")
                if title_el:
                    title = title_el.get_text(strip=True)
                else:
                    continue
            else:
                # Fallback: look for title in card
                title_el = card.select_one("h1, h2, h3, [class*='title']")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
            
            if not title:
                continue

            # Job URL is in a link, usually with text "find out more" or in footer
            link_el = card.select_one("a[href*='/job/']")
            if not link_el:
                # Try footer
                footer = card.select_one("footer[class*='job-card__footer']")
                if footer:
                    link_el = footer.select_one("a[href]")
            
            if not link_el:
                continue
            
            job_url = link_el.get("href", "")
            if job_url and not job_url.startswith("http"):
                job_url = BASE_URL + job_url

            # Company and location are in job-card__body
            body = card.select_one("div[class*='job-card__body']")
            location = "New Zealand"
            company = None
            
            if body:
                body_text = body.get_text()
                # Try to extract location from body text (usually contains location info)
                # Location might be in the text like "Sydney, AUS" or similar
                location_parts = [part.strip() for part in body_text.split() if part.strip()]
                # Look for location patterns
                for i, part in enumerate(location_parts):
                    if ',' in part and i < len(location_parts) - 1:
                        # Might be location
                        location = ' '.join(location_parts[max(0, i-1):i+2])
                        break

            card_text = card.get_text().lower()
            is_remote = any(
                keyword in card_text
                for keyword in ["remote", "work from home", "wfh"]
            )

            job_data = {
                "site": "talentinternational",
                "title": title,
                "company": company,
                "location": location,
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
