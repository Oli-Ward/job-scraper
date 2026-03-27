import pandas as pd
from jobspy import scrape_jobs

TECH_QUERY = (
    '(react OR typescript OR javascript OR node) '
    '"software engineer" OR "software developer" OR "full stack"'
)

def fetch_jobspy_jobs():
    jobs = scrape_jobs(
        site_name=["indeed", "linkedin", "google"],
        search_term=TECH_QUERY,
        google_search_term=(
            "react typescript javascript node software jobs "
            "in New Zealand last 24 hours"
        ),
        location="New Zealand",
        country_indeed="New Zealand",
        hours_old=24,
        is_remote=True,
        results_wanted=50,
        verbose=1,
    )

    df = pd.DataFrame(jobs)
    if df.empty:
        return df

    result_df = pd.DataFrame({
        "site": df["site"],
        "title": df["title"],
        "company": df["company"],
        "location": df["location"],
        "is_remote": df["is_remote"],
        "job_url": df["job_url"],
        "date_posted": df["date_posted"],
        "description": df["description"],
    })

    # Fill empty locations with "New Zealand" as fallback
    result_df["location"] = result_df["location"].fillna("New Zealand")
    result_df["location"] = result_df["location"].replace("", "New Zealand")

    return result_df
