import requests
import pandas as pd
from bs4 import BeautifulSoup
import json
import time
import logging
from sources.validators import validate_and_clean_job

logger = logging.getLogger("JobScraper.Icehouse")

BASE_URL = "https://jobs.icehouseventures.co.nz/jobs"

def fetch_icehouse_jobs():
    """
    Scrapes Icehouse Ventures Jobs listings via static HTML parsing.
    Jobs are available in __NEXT_DATA__ JSON in the initial HTML (no JS rendering needed).
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-NZ,en;q=0.9",
    }
    
    try:
        res = requests.get(BASE_URL, headers=headers, timeout=15)
        res.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Error fetching jobs: {e}")
        return pd.DataFrame()
    
    html = res.text
    if not html:
        return pd.DataFrame()
    
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    
    # Try to extract jobs from __NEXT_DATA__ JSON first (more reliable)
    next_data_script = soup.find("script", id="__NEXT_DATA__")
    if next_data_script:
        try:
            next_data = json.loads(next_data_script.string)
            jobs_data = next_data.get("props", {}).get("pageProps", {}).get("initialState", {}).get("jobs", {}).get("found", [])
            
            for job in jobs_data:
                try:
                    title = job.get("title", "")
                    if not title:
                        continue
                    
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
                    
                    job_url = job.get("url", "")
                    company_name = job.get("organization", {}).get("name", "")
                    locations = job.get("locations", [])
                    location = locations[0] if locations else "New Zealand"
                    work_mode = job.get("workMode", "")
                    is_remote = work_mode == "remote" or "remote" in location.lower()
                    
                    job_data = {
                        "site": "icehouse",
                        "title": title,
                        "company": company_name if company_name else None,
                        "location": location,
                        "is_remote": is_remote,
                        "job_url": job_url,
                        "date_posted": None,
                        "description": None,
                    }
                    
                    validated_job = validate_and_clean_job(job_data)
                    if validated_job:
                        jobs.append(validated_job)
                except Exception as e:
                    logger.debug(f"Error parsing job from JSON: {e}")
                    continue
            
            if jobs:
                time.sleep(1)
                return pd.DataFrame(jobs)
        except (json.JSONDecodeError, KeyError) as e:
            logger.debug(f"Error parsing __NEXT_DATA__: {e}")
    
    # Fallback: Try to find job cards in HTML
    job_cards = soup.select("div[class*='job-card']")
    
    if not job_cards:
        logger.debug("No job cards found - page may not have loaded properly")
        return pd.DataFrame()
    
    for card in job_cards:
        try:
            title_el = card.select_one("a[href*='/job/'], a[href*='seek.co.nz']")
            if not title_el:
                continue
            
            title = title_el.get_text(strip=True)
            if not title:
                continue
            
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
                job_url = "https://jobs.icehouseventures.co.nz" + job_url
            
            company_el = card.select_one("span[class*='company'], div[class*='company']")
            location_el = card.select_one("span[class*='location'], div[class*='location']")
            
            card_text = card.get_text().lower()
            is_remote = any(
                keyword in card_text
                for keyword in ["remote", "work from home", "wfh"]
            )
            
            job_data = {
                "site": "icehouse",
                "title": title,
                "company": company_el.get_text(strip=True) if company_el else None,
                "location": location_el.get_text(strip=True) if location_el else "New Zealand",
                "is_remote": is_remote,
                "job_url": job_url,
                "date_posted": None,
                "description": None,
            }
            
            validated_job = validate_and_clean_job(job_data)
            if validated_job:
                jobs.append(validated_job)
        except Exception as e:
            logger.debug(f"Error parsing job card: {e}")
            continue
    
    time.sleep(1)
    return pd.DataFrame(jobs)
