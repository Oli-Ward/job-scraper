import pandas as pd
import logging
import os
import time
# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, will use system environment variables only
    pass
from sources.jobspy_source import fetch_jobspy_jobs
from sources.seek.init import fetch_seek_jobs
from sources.trademe.init import fetch_trademe_jobs
# Phase 1: High-Priority Common Sites
from sources.robertwalters.init import fetch_robertwalters_jobs
from sources.roberthalf.init import fetch_roberthalf_jobs
from sources.absoluteit.init import fetch_absoluteit_jobs
from sources.recruitit.init import fetch_recruitit_jobs
from sources.beyondrecruitment.init import fetch_beyondrecruitment_jobs
from sources.potentia.init import fetch_potentia_jobs
from sources.talentinternational.init import fetch_talentinternational_jobs
from sources.matchstiq.init import fetch_matchstiq_jobs
# Phase 2: Tech-Focused Platforms
from sources.arcdev.init import fetch_arcdev_jobs
from sources.unicornfactory.init import fetch_unicornfactory_jobs
from sources.zealancer.init import fetch_zealancer_jobs
from sources.toptal.init import fetch_toptal_jobs
from sources.turing.init import fetch_turing_jobs
from sources.icehouse.init import fetch_icehouse_jobs
# Phase 3: NZ-Specific Job Boards
from sources.jobsgovernment.init import fetch_jobsgovernment_jobs
from sources.jobted.init import fetch_jobted_jobs
from sources.jobspace.init import fetch_jobspace_jobs
from sources.sunstonetalent.init import fetch_sunstonetalent_jobs
from sources.dogoodjobs.init import fetch_dogoodjobs_jobs
from sources.rwajobs.init import fetch_rwajobs_jobs
# Phase 4: Additional Agencies
from sources.younity.init import fetch_younity_jobs
from sources.sourced.init import fetch_sourced_jobs
from sources.crescentconsulting.init import fetch_crescentconsulting_jobs
from sources.socialitex.init import fetch_socialitex_jobs
from sources.tribe.init import fetch_tribe_jobs
from sources.trimble.init import fetch_trimble_jobs
from storage.sqlite import init_db, insert_jobs

# Set up logging to match jobspy format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("JobScraper")

def safe_fetch(source_name, fetch_func):
    """
    Safely execute a fetch function, returning empty DataFrame on any error.
    Returns tuple of (DataFrame, elapsed_time, job_count) for summary tracking.
    """
    start_time = time.time()
    try:
        logger.info(f"{source_name} - started scraping")
        df = fetch_func()
        elapsed_time = time.time() - start_time
        job_count = len(df) if df is not None and not df.empty else 0
        logger.info(f"{source_name} - finished scraping ({job_count} jobs found, {elapsed_time:.1f}s)")
        result_df = df if df is not None and not df.empty else pd.DataFrame()
        return result_df, elapsed_time, job_count
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.warning(f"{source_name} - error: {str(e)} (took {elapsed_time:.1f}s)")
        return pd.DataFrame(), elapsed_time, 0

def main():
    init_db()

    # Read disabled sites from environment
    disabled_sites_str = os.getenv("DISABLE_SITES", "")
    disabled_sites = [s.strip() for s in disabled_sites_str.split(",") if s.strip()]
    
    if disabled_sites:
        logger.info(f"Disabled sites: {', '.join(disabled_sites)}")

    # Define all sources with their display names
    sources = [
        # Existing sources
        ("JobSpy", fetch_jobspy_jobs),
        ("Seek", fetch_seek_jobs),
        ("Trade Me", fetch_trademe_jobs),
        # Phase 1: High-Priority Common Sites
        ("Robert Walters", fetch_robertwalters_jobs),
        ("Robert Half", fetch_roberthalf_jobs),
        ("Absolute IT", fetch_absoluteit_jobs),
        ("Recruit IT", fetch_recruitit_jobs),
        ("Beyond Recruitment", fetch_beyondrecruitment_jobs),
        ("Potentia", fetch_potentia_jobs),
        ("Talent International", fetch_talentinternational_jobs),
        ("Matchstiq", fetch_matchstiq_jobs),
        # Phase 2: Tech-Focused Platforms
        ("Arc.dev", fetch_arcdev_jobs),
        ("Unicorn Factory", fetch_unicornfactory_jobs),
        ("Zealancer", fetch_zealancer_jobs),
        ("Toptal", fetch_toptal_jobs),
        ("Turing", fetch_turing_jobs),
        ("Icehouse Ventures", fetch_icehouse_jobs),
        # Phase 3: NZ-Specific Job Boards
        ("Jobs Government", fetch_jobsgovernment_jobs),
        ("Jobted", fetch_jobted_jobs),
        ("JobSpace", fetch_jobspace_jobs),
        ("Sunstone Talent", fetch_sunstonetalent_jobs),
        ("Do Good Jobs", fetch_dogoodjobs_jobs),
        ("RWA Jobs", fetch_rwajobs_jobs),
        # Phase 4: Additional Agencies
        ("Younity", fetch_younity_jobs),
        ("Sourced", fetch_sourced_jobs),
        ("Crescent Consulting", fetch_crescentconsulting_jobs),
        ("Socialite X", fetch_socialitex_jobs),
        ("Tribe", fetch_tribe_jobs),
        ("Trimble", fetch_trimble_jobs),
    ]

    # Filter out disabled sites
    active_sources = [(name, func) for name, func in sources if name not in disabled_sites]
    
    if disabled_sites:
        skipped_count = len(sources) - len(active_sources)
        logger.info(f"Skipped {skipped_count} disabled site(s)")

    # Fetch from all sources safely and track timing/job counts for summary
    results = [safe_fetch(name, func) for name, func in active_sources]
    dfs = [result[0] for result in results]
    
    # Track summary data: (source_name, elapsed_time, job_count)
    summary_data = [(name, results[i][1], results[i][2]) for i, (name, _) in enumerate(active_sources)]

    # Combine all results
    df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    
    if not df.empty:
        # Get excluded keywords from environment
        exclude_keywords_str = os.getenv("EXCLUDE_JOB_KEYWORDS", "qa,junior,senior")
        exclude_keywords = [
            kw.strip().lower() 
            for kw in exclude_keywords_str.split(",")
            if kw.strip()
        ]
        
        # Filter jobs by excluded keywords before inserting
        if exclude_keywords:
            before_count = len(df)
            for keyword in exclude_keywords:
                df = df[~df['title'].str.lower().str.contains(keyword, na=False)]
            filtered_count = before_count - len(df)
            if filtered_count > 0:
                logger.info(f"Filtered out {filtered_count} jobs with excluded keywords: {', '.join(exclude_keywords)}")
        
        df = df.drop_duplicates(subset=["job_url"])
        inserted = insert_jobs(df)
        logger.info(f"Total: Inserted {inserted} new jobs")
    else:
        logger.warning("Total: No jobs found from any source")
    
    # Display summary of problematic scrapers
    slow_scrapers = [(name, elapsed, count) for name, elapsed, count in summary_data if elapsed > 60]
    zero_job_scrapers = [(name, elapsed, count) for name, elapsed, count in summary_data if count == 0]
    
    if slow_scrapers:
        logger.info("=" * 80)
        logger.info("Scrapers that took over 60 seconds:")
        for name, elapsed, count in sorted(slow_scrapers, key=lambda x: x[1], reverse=True):
            logger.info(f"  - {name}: {elapsed:.1f}s ({count} jobs)")
        logger.info("=" * 80)
    
    if zero_job_scrapers:
        logger.info("=" * 80)
        logger.info("Scrapers that returned 0 jobs:")
        for name, elapsed, count in sorted(zero_job_scrapers, key=lambda x: x[1], reverse=True):
            logger.info(f"  - {name}: {elapsed:.1f}s")
        logger.info("=" * 80)

if __name__ == "__main__":
    main()