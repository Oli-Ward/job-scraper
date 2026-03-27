import pandas as pd
from bs4 import BeautifulSoup
import time
import logging
from sources.validators import validate_and_clean_job
from sources.browser_utils import fetch_html

logger = logging.getLogger("JobScraper.RecruitIt")

BASE_URL = "https://www.recruitit.co.nz"

def fetch_recruitit_jobs():
    """
    Scrapes Recruit IT job listings via JavaScript rendering (jobs load dynamically).
    """
    # Jobs page requires JavaScript to load job listings
    url = f"{BASE_URL}/jobs"
    
    # Use JavaScript rendering - jobs are loaded dynamically
    html = fetch_html(
        url,
        use_js=True,
        wait_selector="div[class*='job'], article[class*='job'], div[class*='position'], div[class*='listing']",
        timeout=60,  # 60 seconds (converted to milliseconds by fetch_html)
        wait_until="load"  # Wait for page load instead of networkidle
    )
    
    if not html:
        return pd.DataFrame()
    
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    
    # Recruit IT job listings are links with /job-details/ in href
    # Find all links that point to job details pages
    job_links = soup.find_all("a", href=True)
    job_listings = [link for link in job_links if "/job-details/" in link.get("href", "")]
    
    if not job_listings:
        logger.debug("No job listings found - page may require search or jobs may not be loaded")
        return pd.DataFrame()

    for link in job_listings:
        try:
            # Skip navigation and action links
            link_text = link.get_text(strip=True).lower()
            skip_texts = ["job search", "jobseekers", "jobs", "read more", "send email", "apply", "view"]
            if any(skip in link_text for skip in skip_texts):
                continue
            
            title = link.get_text(strip=True)
            # Skip if title is empty or too short (likely navigation/action button)
            if not title or len(title) < 5:
                continue
            
            job_url = link.get("href", "")
            if job_url and not job_url.startswith("http"):
                job_url = BASE_URL + job_url
            
            # Skip if job_url is empty, doesn't contain job-details, or is mailto
            if not job_url or "/job-details/" not in job_url or job_url.startswith("mailto:"):
                continue
            
            # Try to find parent container for company/location info
            parent = link.find_parent(["div", "article", "li"])
            card = parent if parent else link

            # Company and location may be in nearby elements
            company_el = (
                card.select_one("span[class*='company']") or
                card.select_one("div[class*='company']") or
                card.find_next("span", class_=lambda x: x and "company" in x.lower()) or
                card.find_next("div", class_=lambda x: x and "company" in x.lower())
            )

            location_el = (
                card.select_one("span[class*='location']") or
                card.select_one("div[class*='location']") or
                card.find_next("span", class_=lambda x: x and "location" in x.lower()) or
                card.find_next("div", class_=lambda x: x and "location" in x.lower())
            )

            # Check for remote in title or nearby text
            card_text = (title + " " + (card.get_text() if card else "")).lower()
            is_remote = any(
                keyword in card_text
                for keyword in ["remote", "work from home", "wfh"]
            )

            job_data = {
                "site": "recruitit",
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
