import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import time
import logging
from sources.validators import validate_and_clean_job

logger = logging.getLogger("JobScraper.RobertWalters")

BASE_URL = "https://www.robertwalters.co.nz/jobs.html"

def fetch_robertwalters_jobs():
    """
    Scrapes Robert Walters NZ job listings via HTML parsing.
    Note: This site may use Cloudflare or similar protection that blocks automated requests.
    """
    # Use session for better cookie handling
    session = requests.Session()
    
    # More realistic browser headers
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-NZ,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    
    session.headers.update(headers)
    
    # First, try to visit the main page to establish session and get cookies
    try:
        main_page = session.get("https://www.robertwalters.co.nz/", timeout=15, allow_redirects=True)
        time.sleep(1)  # Delay to appear more human-like
        
        # Update referer after visiting main page
        session.headers.update({"Referer": "https://www.robertwalters.co.nz/"})
    except Exception as e:
        logger.debug(f"Could not establish session on main page: {e}")

    params = {
        "q": "react typescript javascript node software",
    }

    url = f"{BASE_URL}?{urlencode(params)}"

    try:
        res = session.get(url, timeout=15, allow_redirects=True)
        res.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Error fetching jobs page (403 likely indicates bot protection): {e}")
        # Try without query parameters as fallback
        try:
            time.sleep(1)
            res = session.get(BASE_URL, timeout=15, allow_redirects=True)
            res.raise_for_status()
        except requests.RequestException as e2:
            logger.warning(f"Error fetching fallback page: {e2}")
            # Robert Walters appears to be blocking automated requests
            # This may require Selenium/Playwright or manual inspection
            return pd.DataFrame()

    soup = BeautifulSoup(res.text, "html.parser")
    jobs = []

    # Try multiple selectors for job cards
    job_cards = (
        soup.select("div.job-card") or
        soup.select("article.job-listing") or
        soup.select("div[class*='job']") or
        soup.select("li[class*='job']")
    )

    for card in job_cards:
        try:
            # Try multiple selectors for title
            title_el = (
                card.select_one("a[href*='/job/']") or
                card.select_one("h2 a") or
                card.select_one("h3 a") or
                card.select_one("a.job-title")
            )
            
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            job_url = title_el.get("href", "")
            if job_url and not job_url.startswith("http"):
                job_url = "https://www.robertwalters.co.nz" + job_url

            # Try multiple selectors for company
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
                "site": "robertwalters",
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
