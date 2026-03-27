import pandas as pd
from bs4 import BeautifulSoup
import time
import logging
import re
from sources.validators import validate_and_clean_job
from sources.browser_utils import fetch_html

logger = logging.getLogger("JobScraper.Matchstiq")

BASE_URL = "https://matchstiq.io"

def fetch_matchstiq_jobs():
    """
    Scrapes Matchstiq job listings via JavaScript rendering (SPA).
    Jobs are in div.c-card elements with h4 titles.
    """
    # Try the main jobs page
    url = f"{BASE_URL}/jobs"
    
    # Matchstiq is a SPA - use JavaScript rendering
    # Don't wait for selector as it may timeout - use domcontentloaded for faster loading
    html = fetch_html(
        url,
        use_js=True,
        wait_selector=None,  # Don't wait for selector to avoid timeout
        timeout=60,
        wait_until="domcontentloaded"  # Use domcontentloaded for faster page load
    )
    
    if not html:
        return pd.DataFrame()
    
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    
    # Matchstiq job cards are div.c-card elements that contain h4 titles
    all_cards = soup.select("div.c-card")
    job_cards = []
    for card in all_cards:
        # Filter to only actual job cards (they have h4 titles)
        h4 = card.select_one("h4")
        if h4 and h4.get_text(strip=True):
            job_cards.append(card)

    if not job_cards:
        logger.debug("No job cards found - page may not have loaded properly")
        return pd.DataFrame()
    
    for card in job_cards:
        try:
            # Title is in h4
            title_el = card.select_one("h4")
            if not title_el:
                continue
            
            title = title_el.get_text(strip=True)
            if not title:
                continue
            
            # Construct job URL from title slug (cards don't have direct links)
            slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
            job_url = f"{BASE_URL}/jobs/{slug}"

            # Company name is often in image alt text or can be extracted from text
            company = None
            company_img = card.select_one("img[alt]")
            if company_img:
                alt = company_img.get("alt", "")
                # Remove file extension and clean up
                company = alt.replace("-logo-v2.png", "").replace("-logo.png", "").replace(".png", "").replace(".jpg", "").strip()
            
            # Extract location from card text
            # Location usually appears after company name in the text
            card_text = card.get_text()
            location = "New Zealand"
            
            # Look for location patterns in text
            # Common patterns: "Sydney", "Auckland", "Remote", "Sydney, AUS", etc.
            location_keywords = [
                "Auckland", "Wellington", "Christchurch", "Dunedin", "Hamilton", 
                "Tauranga", "New Zealand", "NZ", "Sydney", "Melbourne", "Brisbane",
                "Perth", "Adelaide", "Canberra", "Remote", "Anywhere"
            ]
            
            # Split text into lines and look for location
            lines = [line.strip() for line in card_text.split('\n') if line.strip()]
            for line in lines:
                line_lower = line.lower()
                # Look for location keywords in short lines (locations are usually brief)
                if len(line) < 80 and any(keyword.lower() in line_lower for keyword in location_keywords):
                    # Extract just the location part (before any long description)
                    location_parts = []
                    for keyword in location_keywords:
                        if keyword.lower() in line_lower:
                            # Try to extract the location with context
                            idx = line_lower.find(keyword.lower())
                            # Get a reasonable chunk around the keyword
                            start = max(0, idx - 20)
                            end = min(len(line), idx + len(keyword) + 20)
                            location_candidate = line[start:end].strip()
                            if len(location_candidate) < 60:  # Keep it short
                                location_parts.append(location_candidate)
                    if location_parts:
                        location = location_parts[0]  # Take first match
                        break
            
            # Check if remote
            is_remote = any(
                keyword in card_text.lower()
                for keyword in ["remote", "work from home", "wfh", "anywhere"]
            )

            job_data = {
                "site": "matchstiq",
                "title": title,
                "company": company if company else None,
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
