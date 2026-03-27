#!/usr/bin/env python3
"""
Test a single job website and display results in a formatted terminal output.

Usage:
    python test_single_site.py "Trade Me"
    python test_single_site.py trademe
    python test_single_site.py "Robert Walters"
"""

import sys
import pandas as pd
import logging
from datetime import datetime
from tabulate import tabulate

# Set up logging to only show warnings/errors
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Import all scrapers
from sources.jobspy_source import fetch_jobspy_jobs
from sources.seek.init import fetch_seek_jobs
from sources.trademe.init import fetch_trademe_jobs
from sources.robertwalters.init import fetch_robertwalters_jobs
from sources.roberthalf.init import fetch_roberthalf_jobs
from sources.absoluteit.init import fetch_absoluteit_jobs
from sources.recruitit.init import fetch_recruitit_jobs
from sources.beyondrecruitment.init import fetch_beyondrecruitment_jobs
from sources.potentia.init import fetch_potentia_jobs
from sources.talentinternational.init import fetch_talentinternational_jobs
from sources.matchstiq.init import fetch_matchstiq_jobs
from sources.arcdev.init import fetch_arcdev_jobs
from sources.unicornfactory.init import fetch_unicornfactory_jobs
from sources.zealancer.init import fetch_zealancer_jobs
from sources.toptal.init import fetch_toptal_jobs
from sources.turing.init import fetch_turing_jobs
from sources.icehouse.init import fetch_icehouse_jobs
from sources.jobsgovernment.init import fetch_jobsgovernment_jobs
from sources.jobted.init import fetch_jobted_jobs
from sources.jobspace.init import fetch_jobspace_jobs
from sources.sunstonetalent.init import fetch_sunstonetalent_jobs
from sources.dogoodjobs.init import fetch_dogoodjobs_jobs
from sources.rwajobs.init import fetch_rwajobs_jobs
from sources.younity.init import fetch_younity_jobs
from sources.sourced.init import fetch_sourced_jobs
from sources.crescentconsulting.init import fetch_crescentconsulting_jobs
from sources.socialitex.init import fetch_socialitex_jobs
from sources.tribe.init import fetch_tribe_jobs
from sources.trimble.init import fetch_trimble_jobs

# Map site names (case-insensitive) to fetch functions
SITE_MAP = {
    "jobspy": fetch_jobspy_jobs,
    "seek": fetch_seek_jobs,
    "trademe": fetch_trademe_jobs,
    "trade me": fetch_trademe_jobs,
    "robert walters": fetch_robertwalters_jobs,
    "robertwalters": fetch_robertwalters_jobs,
    "robert half": fetch_roberthalf_jobs,
    "roberthalf": fetch_roberthalf_jobs,
    "absolute it": fetch_absoluteit_jobs,
    "absoluteit": fetch_absoluteit_jobs,
    "recruit it": fetch_recruitit_jobs,
    "recruitit": fetch_recruitit_jobs,
    "beyond recruitment": fetch_beyondrecruitment_jobs,
    "beyondrecruitment": fetch_beyondrecruitment_jobs,
    "potentia": fetch_potentia_jobs,
    "talent international": fetch_talentinternational_jobs,
    "talentinternational": fetch_talentinternational_jobs,
    "matchstiq": fetch_matchstiq_jobs,
    "arc.dev": fetch_arcdev_jobs,
    "arcdev": fetch_arcdev_jobs,
    "unicorn factory": fetch_unicornfactory_jobs,
    "unicornfactory": fetch_unicornfactory_jobs,
    "zealancer": fetch_zealancer_jobs,
    "toptal": fetch_toptal_jobs,
    "turing": fetch_turing_jobs,
    "icehouse ventures": fetch_icehouse_jobs,
    "icehouse": fetch_icehouse_jobs,
    "jobs government": fetch_jobsgovernment_jobs,
    "jobsgovernment": fetch_jobsgovernment_jobs,
    "jobted": fetch_jobted_jobs,
    "jobspace": fetch_jobspace_jobs,
    "sunstone talent": fetch_sunstonetalent_jobs,
    "sunstonetalent": fetch_sunstonetalent_jobs,
    "do good jobs": fetch_dogoodjobs_jobs,
    "dogoodjobs": fetch_dogoodjobs_jobs,
    "rwa jobs": fetch_rwajobs_jobs,
    "rwajobs": fetch_rwajobs_jobs,
    "younity": fetch_younity_jobs,
    "sourced": fetch_sourced_jobs,
    "crescent consulting": fetch_crescentconsulting_jobs,
    "crescentconsulting": fetch_crescentconsulting_jobs,
    "socialite x": fetch_socialitex_jobs,
    "socialitex": fetch_socialitex_jobs,
    "tribe": fetch_tribe_jobs,
    "trimble": fetch_trimble_jobs,
}

def find_site_function(site_name):
    """Find the fetch function for a given site name (case-insensitive)."""
    site_lower = site_name.lower().strip()
    
    # Direct match
    if site_lower in SITE_MAP:
        return SITE_MAP[site_lower], site_name
    
    # Try partial matches
    for key, func in SITE_MAP.items():
        if site_lower in key or key in site_lower:
            return func, key
    
    return None, None

def format_job_table(df, max_rows=20):
    """Format jobs DataFrame as a nice table."""
    if df.empty:
        return "No jobs found."
    
    # Select columns to display
    display_cols = ['title', 'company', 'location', 'is_remote', 'job_url']
    available_cols = [col for col in display_cols if col in df.columns]
    
    # Limit rows
    display_df = df[available_cols].head(max_rows).copy()
    
    # Format is_remote as Yes/No
    if 'is_remote' in display_df.columns:
        display_df['is_remote'] = display_df['is_remote'].apply(lambda x: 'Yes' if x else 'No')
    
    # Truncate long URLs for display
    if 'job_url' in display_df.columns:
        display_df['job_url'] = display_df['job_url'].apply(
            lambda x: x[:60] + '...' if len(str(x)) > 60 else x
        )
    
    # Truncate long titles
    if 'title' in display_df.columns:
        display_df['title'] = display_df['title'].apply(
            lambda x: x[:50] + '...' if len(str(x)) > 50 else x
        )
    
    return tabulate(display_df, headers='keys', tablefmt='grid', showindex=False)

def test_site(site_name):
    """Test a single site and display results."""
    print("=" * 80)
    print(f"Testing: {site_name}")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Find the fetch function
    fetch_func, matched_name = find_site_function(site_name)
    
    if not fetch_func:
        print(f"❌ Error: Site '{site_name}' not found.")
        print()
        print("Available sites:")
        for key in sorted(SITE_MAP.keys()):
            print(f"  - {key}")
        return
    
    if matched_name != site_name:
        print(f"ℹ️  Matched to: {matched_name}")
        print()
    
    # Fetch jobs
    print("🔄 Fetching jobs...")
    try:
        start_time = datetime.now()
        df = fetch_func()
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if df is None or df.empty:
            print(f"⚠️  No jobs found (took {elapsed:.1f}s)")
            return
        
        job_count = len(df)
        print(f"✅ Found {job_count} job(s) (took {elapsed:.1f}s)")
        print()
        
        # Display summary
        print("📊 Summary:")
        print(f"  Total jobs: {job_count}")
        
        if 'is_remote' in df.columns:
            remote_count = df['is_remote'].sum() if df['is_remote'].dtype == bool else 0
            print(f"  Remote jobs: {remote_count}")
        
        if 'location' in df.columns:
            locations = df['location'].value_counts().head(5)
            if not locations.empty:
                print(f"  Top locations:")
                for loc, count in locations.items():
                    print(f"    - {loc}: {count}")
        
        print()
        print("📋 Jobs:")
        print()
        print(format_job_table(df))
        
        if job_count > 20:
            print()
            print(f"... and {job_count - 20} more job(s)")
        
        print()
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        print()
        print("Traceback:")
        traceback.print_exc()
        print()
        print("=" * 80)

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_single_site.py <site_name>")
        print()
        print("Examples:")
        print('  python test_single_site.py "Trade Me"')
        print('  python test_single_site.py trademe')
        print('  python test_single_site.py "Robert Walters"')
        print()
        print("Available sites:")
        for key in sorted(SITE_MAP.keys()):
            print(f"  - {key}")
        sys.exit(1)
    
    site_name = " ".join(sys.argv[1:])
    test_site(site_name)

if __name__ == "__main__":
    main()
