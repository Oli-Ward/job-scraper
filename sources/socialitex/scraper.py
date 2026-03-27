import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import logging
from sources.validators import validate_and_clean_job

logger = logging.getLogger("JobScraper.SocialiteX")

BASE_URL = "https://www.socialitenz.com"

def fetch_socialitex_jobs():
    """
    Scrapes Socialite X job listings via HTML parsing.
    """
    search_paths = [
        "/current-opportunities",
        "/job-search",
        "/vacancies",
        "/jobs",
        "/careers",
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

                        card_text = card.get_text().lower()
                        is_remote = any(
                            keyword in card_text
                            for keyword in ["remote", "work from home", "wfh"]
                        )

                        job_data = {
                            "site": "socialitex",
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
                
                if jobs:
                    break
                    
        except requests.RequestException:
            continue
        except Exception as e:
            logger.warning(f"Error fetching jobs: {e}")
            continue

    time.sleep(1)
    return pd.DataFrame(jobs)
