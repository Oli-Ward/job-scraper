import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import time
import logging
from sources.validators import validate_and_clean_job

logger = logging.getLogger("JobScraper.JobSpace")

BASE_URL = "https://jobspace.co.nz"

def fetch_jobspace_jobs():
    """
    Scrapes JobSpace NZ job listings via HTML parsing.
    """
    params = {
        "q": "react typescript javascript node software",
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-NZ,en;q=0.9",
    }

    url = f"{BASE_URL}?{urlencode(params)}"

    try:
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Error fetching jobs: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(res.text, "html.parser")
    jobs = []

    job_cards = (
        soup.select("div[class*='job']") or
        soup.select("article[class*='job']") or
        soup.select("li[class*='job']")
    )

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
            
            # Filter for tech-related jobs only
            title_lower = title.lower()
            tech_keywords = [
                "software", "developer", "engineer", "programmer", "programming",
                "react", "typescript", "javascript", "node", "python", "java",
                "full stack", "frontend", "backend", "devops", "it", "ict",
                "technical", "tech", "coding", "code", "application", "web"
            ]
            
            # Skip if title doesn't contain any tech keywords
            if not any(keyword in title_lower for keyword in tech_keywords):
                continue
            
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
                "site": "jobspace",
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
