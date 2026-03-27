import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import logging
import re
from sources.validators import validate_and_clean_job

logger = logging.getLogger("JobScraper.Potentia")

BASE_URL = "https://potentia.co.nz"

def fetch_potentia_jobs():
    """
    Scrapes Potentia job listings via HTML parsing.
    """
    url = f"{BASE_URL}/jobs"

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
        
        # Find all job links - they're in a[href*="/job/"]
        job_links = soup.select('a[href*="/job/"]')
        
        for link in job_links:
            try:
                href = link.get("href", "")
                if not href:
                    continue
                
                # Make URL absolute
                if not href.startswith("http"):
                    job_url = BASE_URL + href
                else:
                    job_url = href
                
                # Extract title from URL slug: /job/{id}-{slug}
                # Example: /job/58998701-cloud-engineer -> "Cloud Engineer"
                slug_match = re.search(r'/job/\d+-(.+)', href)
                if slug_match:
                    slug = slug_match.group(1)
                    title = slug.replace('-', ' ').title()
                else:
                    # Fallback: use link text or "Apply now" -> skip
                    title = link.get_text(strip=True)
                    if not title or title.lower() in ['apply now', 'apply']:
                        continue
                
                # Find location from previous sibling div
                parent = link.find_parent()
                location = "New Zealand"
                if parent:
                    prev_sibling = parent.find_previous_sibling()
                    if prev_sibling:
                        location_text = prev_sibling.get_text(strip=True)
                        # Parse common NZ locations
                        nz_locations = ['Auckland', 'Wellington', 'Christchurch', 'Hamilton', 
                                       'Tauranga', 'Dunedin', 'Palmerston North', 'Napier',
                                       'Rotorua', 'New Plymouth', 'Whangarei', 'Invercargill']
                        for loc in nz_locations:
                            if loc in location_text:
                                location = loc
                                break
                
                # Check for remote
                card_text = (parent.get_text().lower() if parent else "") + title.lower()
                is_remote = any(
                    keyword in card_text
                    for keyword in ["remote", "work from home", "wfh"]
                )

                job_data = {
                    "site": "potentia",
                    "title": title,
                    "company": None,  # Company info not easily available on listing page
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
                logger.debug(f"Error parsing job link: {e}")
                continue
                    
    except requests.RequestException as e:
        logger.warning(f"Error fetching jobs: {e}")
    except Exception as e:
        logger.warning(f"Error parsing jobs page: {e}")

    time.sleep(1)
    return pd.DataFrame(jobs)
