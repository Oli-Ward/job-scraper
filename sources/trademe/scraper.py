import pandas as pd
from bs4 import BeautifulSoup
import time
import logging
from sources.validators import validate_and_clean_job
from sources.browser_utils import fetch_html

logger = logging.getLogger("JobScraper.TradeMe")

BASE_URL = "https://www.trademe.co.nz/a/jobs"

def fetch_trademe_jobs():
    """
    Scrapes Trade Me Jobs via JavaScript rendering (SPA with custom web components).
    Browses the IT/Programming-Development category to get all programming jobs.
    Switch to api.py once API credentials are approved.
    """
    # Browse the IT/Programming-Development category page directly
    # This gets all programming/development jobs without keyword filtering
    url = f"{BASE_URL}/it/programming-development"

    # Trade Me uses custom web components (tm-*) that require JavaScript rendering
    # Use "load" instead of "networkidle" to avoid timeout - networkidle waits for network to be idle
    # which some sites never achieve
    html = fetch_html(
        url,
        use_js=True,
        wait_selector="tm-jobs-search-card, tm-search-card-wrapper, div[data-testid='search-result-card']",
        timeout=60,  # 60 seconds (converted to milliseconds by fetch_html)
        wait_until="load"  # Wait for page load instead of networkidle
    )

    if not html:
        return pd.DataFrame()

    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    # Trade Me job card structure - uses custom web components
    # Try the correct selector for category pages first
    job_cards = soup.select("tm-jobs-search-card")
    
    if not job_cards:
        # Fallback to search results page selector
        job_cards = soup.select("tm-search-card-wrapper")
    
    if not job_cards:
        # Another fallback
        job_cards = soup.select("div[data-testid='search-result-card']")
    
    if not job_cards:
        logger.debug("No job cards found - page may not have loaded properly")
        return pd.DataFrame()

    for card in job_cards:
        try:
            # For category pages, use tm-jobs-search-card structure
            # Title is in div.tm-jobs-search-card__title
            title_el = card.select_one("div.tm-jobs-search-card__title")
            if not title_el:
                # Fallback to search results page selectors
                title_el = card.select_one("a[data-testid='listing-title-link']")
            if not title_el:
                title_el = card.select_one("h3 a")
            
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            
            # URL is in a.tm-jobs-search-card__link for category pages
            link_el = card.select_one("a.tm-jobs-search-card__link")
            if not link_el:
                link_el = title_el if title_el.name == 'a' else title_el.find_parent('a')
            
            job_url = ""
            if link_el:
                job_url = link_el.get("href", "")
            if job_url and not job_url.startswith("http"):
                job_url = "https://www.trademe.co.nz" + job_url

            # Company name - for category pages it's in div.jobs-search-card-metadata__company
            company_el = (
                card.select_one("div.jobs-search-card-metadata__company") or
                card.select_one("span[data-testid='seller-name']") or
                card.select_one("div.tm-job-listing-card__attribute")
            )

            # Location - for category pages it's in div.jobs-search-card-metadata__location
            location_el = (
                card.select_one("div.jobs-search-card-metadata__location") or
                card.select_one("[data-testid='location']") or
                card.select_one("span[class*='location']") or
                card.select_one("div[class*='location']")
            )

            is_remote = any(
                keyword in title.lower()
                for keyword in ["remote", "work from home", "wfh", "flexible location"]
            )

            job_data = {
                "site": "trademe",
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