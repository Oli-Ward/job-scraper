import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import logging
from sources.validators import validate_and_clean_job

logger = logging.getLogger("JobScraper.CrescentConsulting")

BASE_URL = "https://www.crescent.co.nz"

def fetch_crescentconsulting_jobs():
    """
    Scrapes Crescent Consulting job listings via HTML parsing.
    Note: Crescent Consulting uses Bullhorn Reach iframe for job listings.
    We'll try to scrape the iframe content directly.
    """
    # Try the jobs listing page first (has iframe)
    search_paths = [
        "/jobs-listing",  # This is the actual page with the iframe
        "/jobs",
        "/job-search",
        "/vacancies",
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
            
            # Check for iframe with Bullhorn Reach
            iframe = soup.select_one("iframe[src*='bullhornreach']")
            if iframe and path == "/jobs-listing":
                # Try to scrape the iframe URL directly
                iframe_url = iframe.get("src", "")
                if iframe_url:
                    try:
                        iframe_res = requests.get(iframe_url, headers=headers, timeout=15)
                        iframe_res.raise_for_status()
                        iframe_soup = BeautifulSoup(iframe_res.text, "html.parser")
                        job_cards = (
                            iframe_soup.select("div[class*='job']") or
                            iframe_soup.select("article[class*='job']") or
                            iframe_soup.select("li[class*='job']") or
                            iframe_soup.select("div[class*='position']") or
                            iframe_soup.select("div[class*='vacancy']")
                        )
                    except requests.RequestException:
                        job_cards = []
                else:
                    job_cards = []
            else:
                job_cards = (
                    soup.select("div[class*='job']") or
                    soup.select("article[class*='job']") or
                    soup.select("li[class*='job']") or
                    soup.select("div[class*='position']") or
                    soup.select("div[class*='vacancy']")
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
                            "site": "crescentconsulting",
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
