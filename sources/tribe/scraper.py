import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import logging
from sources.validators import validate_and_clean_job

logger = logging.getLogger("JobScraper.Tribe")

BASE_URL = "https://www.tribegroup.com"

def fetch_tribe_jobs():
    """
    Scrapes Tribe job listings via HTML parsing.
    """
    url = f"{BASE_URL}/find-a-job/job-listings"

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

    try:
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Find job listing container
        jobs_container = soup.select_one("div.job-listing__jobs")
        if not jobs_container:
            return pd.DataFrame()
        
        # Find all job card links
        job_links = jobs_container.select("a.job-card[href*='/job-listings/']")
        
        # Filter for real job links (with numeric ID at the end)
        real_job_links = [l for l in job_links if l.get('href', '').split('/')[-1].isdigit()]
        
        for link in real_job_links:
            try:
                href = link.get("href", "")
                if not href:
                    continue
                
                # Make URL absolute
                if not href.startswith("http"):
                    job_url = BASE_URL + href
                else:
                    job_url = href
                
                # Title is in h3.job-card__title
                title_el = link.select_one("h3.job-card__title, .job-card__title")
                if not title_el:
                    continue
                
                title = title_el.get_text(strip=True)
                
                # Location is in div.job-card__tags > div.pill (look for location pill)
                location = "New Zealand"
                tags = link.select("div.job-card__tags div.pill")
                for tag in tags:
                    tag_text = tag.get_text(strip=True)
                    # Common NZ locations
                    nz_locations = ['Auckland', 'Wellington', 'Christchurch', 'Hamilton', 
                                   'Tauranga', 'Dunedin', 'Palmerston North', 'Napier',
                                   'Rotorua', 'New Plymouth', 'Whangarei', 'Invercargill']
                    for loc in nz_locations:
                        if loc in tag_text:
                            location = loc
                            break
                    if location != "New Zealand":
                        break
                
                # Date posted
                date_el = link.select_one("div.job-card__date")
                date_posted = date_el.get_text(strip=True) if date_el else None
                
                # Check for remote/hybrid
                card_text = link.get_text().lower()
                is_remote = any(
                    keyword in card_text
                    for keyword in ["remote", "work from home", "wfh", "hybrid"]
                )
                
                # Company not easily available on listing page
                company = None

                job_data = {
                    "site": "tribe",
                    "title": title,
                    "company": company,
                    "location": location,
                    "is_remote": is_remote,
                    "job_url": job_url,
                    "date_posted": date_posted,
                    "description": None,
                }

                # Validate and clean job data
                validated_job = validate_and_clean_job(job_data)
                if validated_job:
                    jobs.append(validated_job)

            except Exception as e:
                logger.debug(f"Error parsing job link: {e}")
                continue

    except requests.RequestException as e:
        logger.warning(f"Error fetching jobs: {e}")
    except Exception as e:
        logger.warning(f"Error parsing jobs page: {e}")

    time.sleep(1)
    return pd.DataFrame(jobs)
