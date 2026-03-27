import requests
import pandas as pd
from requests_oauthlib import OAuth1

# Set as environment variables once approved
TRADEME_CONSUMER_KEY = None  # os.getenv("TRADEME_CONSUMER_KEY")
TRADEME_CONSUMER_SECRET = None  # os.getenv("TRADEME_CONSUMER_SECRET")

API_BASE = "https://api.trademe.co.nz/v1"

def fetch_trademe_jobs():
    """
    Official Trade Me API implementation using OAuth 1.0a.
    Docs: https://developer.trademe.co.nz/api-overview/
    """
    if not TRADEME_CONSUMER_KEY or not TRADEME_CONSUMER_SECRET:
        raise ValueError("Trade Me API credentials not configured")

    auth = OAuth1(TRADEME_CONSUMER_KEY, TRADEME_CONSUMER_SECRET)

    params = {
        "search_string": "react typescript javascript node",
        "rows": 50,
        "category": "5000-",  # Jobs category
    }

    res = requests.get(
        f"{API_BASE}/Search/Jobs.json",
        auth=auth,
        params=params,
        timeout=15
    )
    res.raise_for_status()

    data = res.json()
    jobs = []

    for j in data.get("List", []):
        jobs.append({
            "site": "trademe",
            "title": j.get("Title"),
            "company": j.get("Agency", {}).get("Name"),
            "location": j.get("Suburb") or j.get("District") or "New Zealand",
            "is_remote": "remote" in j.get("Title", "").lower(),
            "job_url": f"https://www.trademe.co.nz/a/jobs/{j.get('ListingId')}",
            "date_posted": j.get("StartDate"),
            "description": j.get("Body"),
        })

    return pd.DataFrame(jobs)