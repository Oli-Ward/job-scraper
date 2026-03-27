import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import logging
import re
from sources.validators import validate_and_clean_job

logger = logging.getLogger("JobScraper.ArcDev")

BASE_URL = "https://arc.dev"

def fetch_arcdev_jobs():
    """
    Scrapes Arc.dev job listings via HTML parsing.
    Note: This may be a SPA requiring JavaScript rendering.
    """
    search_paths = [
        "/jobs",
        "/job-search",
        "/remote-jobs",
    ]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-NZ,en;q=0.9",
    }

    jobs = []

    for path in search_paths:
        url = f"{BASE_URL}{path}"
        try:
            res = requests.get(url, headers=headers, timeout=15)
            res.raise_for_status()
            
            soup = BeautifulSoup(res.text, "html.parser")
            
            job_cards = (
                soup.select("div[class*='job']") or
                soup.select("article[class*='job']") or
                soup.select("li[class*='job']")
            )

            if job_cards:
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

                        location_text = location_el.get_text(strip=True) if location_el else ""
                        
                        # Filter for NZ/AU timezones only
                        # NZ is GMT+12/GMT+13, AU is GMT+8 to GMT+11
                        # Accept timezones that overlap with NZ/AU (GMT+8 to GMT+13)
                        location_lower = location_text.lower()
                        card_text = card.get_text().lower()
                        
                        # Check if location mentions timezone
                        has_timezone = "gmt" in location_lower or "timezone" in location_lower or "time zone" in location_lower
                        
                        if has_timezone:
                            # Extract GMT offset if present
                            import re
                            gmt_matches = re.findall(r'gmt[+\-]?(\d+)', location_lower)
                            if gmt_matches:
                                # Check if any GMT offset is in NZ/AU range (8-13)
                                gmt_values = [int(m) for m in gmt_matches]
                                # Accept if any timezone in the range overlaps with NZ/AU
                                # For ranges like "GMT+2 to GMT+6", we want to skip
                                # For ranges like "GMT+8 to GMT+12", we want to include
                                min_gmt = min(gmt_values) if gmt_values else 0
                                max_gmt = max(gmt_values) if gmt_values else 0
                                
                                # Only include if range overlaps with NZ/AU (8-13)
                                if max_gmt < 8 or min_gmt > 13:
                                    continue  # Skip jobs outside NZ/AU timezone range
                        
                        # Arc.dev focuses on remote jobs
                        is_remote = "remote" in card_text or "work from home" in card_text or "wfh" in card_text

                        job_data = {
                            "site": "arcdev",
                            "title": title,
                            "company": company_el.get_text(strip=True) if company_el else None,
                            "location": location_text if location_text else "Remote",
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
                
                if jobs:
                    break
                    
        except requests.RequestException:
            continue
        except Exception as e:
            logger.warning(f"Error fetching jobs: {e}")
            continue

    time.sleep(1)
    return pd.DataFrame(jobs)
