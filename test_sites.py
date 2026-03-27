#!/usr/bin/env python3
"""
Test script to verify all job sites are working.
Tests each site and reports:
- Sites that return jobs (WORKING)
- Sites that return 0 jobs (may be filtering or site issue)
- Sites that error/timeout (BROKEN/BLOCKED)
"""
import pandas as pd
import logging
import sys
from datetime import datetime

# Import all scrapers
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

# Set up logging
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings/errors during testing
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def test_site(name, fetch_func):
    """
    Test a single site and return status information.
    """
    try:
        df = fetch_func()
        if df is None or df.empty:
            return {
                "status": "ZERO_RESULTS",
                "count": 0,
                "error": None,
                "sample_titles": []
            }
        else:
            sample_titles = df['title'].head(3).tolist() if 'title' in df.columns else []
            return {
                "status": "WORKING",
                "count": len(df),
                "error": None,
                "sample_titles": sample_titles
            }
    except Exception as e:
        error_msg = str(e)
        # Classify error types
        if "403" in error_msg or "Forbidden" in error_msg:
            status = "BLOCKED"
        elif "timeout" in error_msg.lower() or "Timeout" in error_msg:
            status = "TIMEOUT"
        elif "404" in error_msg or "Not Found" in error_msg:
            status = "NOT_FOUND"
        else:
            status = "ERROR"
        
        return {
            "status": status,
            "count": 0,
            "error": error_msg[:100],  # Truncate long error messages
            "sample_titles": []
        }

def main():
    """
    Test all sites and generate a report.
    """
    print("=" * 70)
    print("Job Site Testing Report")
    print("=" * 70)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Testing all sites with current search terms...")
    print("(Note: Sites returning 0 jobs may be due to strict filtering)")
    print()
    
    # Define all sources
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
    
    results = []
    
    for name, func in sources:
        print(f"Testing {name}...", end=" ", flush=True)
        result = test_site(name, func)
        result["name"] = name
        results.append(result)
        
        # Print quick status
        if result["status"] == "WORKING":
            print(f"✓ {result['count']} jobs")
        elif result["status"] == "ZERO_RESULTS":
            print("⚠ 0 jobs (may be filtering)")
        else:
            print(f"✗ {result['status']}")
    
    print()
    print("=" * 70)
    print("Detailed Results")
    print("=" * 70)
    print()
    
    # Group results by status
    working = [r for r in results if r["status"] == "WORKING"]
    zero_results = [r for r in results if r["status"] == "ZERO_RESULTS"]
    blocked = [r for r in results if r["status"] == "BLOCKED"]
    timeout = [r for r in results if r["status"] == "TIMEOUT"]
    errors = [r for r in results if r["status"] in ["ERROR", "NOT_FOUND"]]
    
    # Print working sites
    if working:
        print("✓ WORKING SITES:")
        print("-" * 70)
        for r in sorted(working, key=lambda x: x["count"], reverse=True):
            print(f"  {r['name']:30} {r['count']:4} jobs")
            if r['sample_titles']:
                for title in r['sample_titles'][:2]:
                    print(f"    - {title[:60]}")
        print()
    
    # Print zero result sites
    if zero_results:
        print("⚠ ZERO RESULTS (May be due to strict filtering):")
        print("-" * 70)
        for r in zero_results:
            print(f"  {r['name']}")
            print("    → Site may be working but no jobs match current search terms")
            print("    → Try testing with general terms like 'software' or 'developer'")
        print()
    
    # Print blocked sites
    if blocked:
        print("✗ BLOCKED SITES (403 Forbidden - likely bot protection):")
        print("-" * 70)
        for r in blocked:
            print(f"  {r['name']}")
            if r['error']:
                print(f"    Error: {r['error']}")
            print("    → Consider adding to DISABLE_SITES or using proxy")
        print()
    
    # Print timeout sites
    if timeout:
        print("✗ TIMEOUT SITES:")
        print("-" * 70)
        for r in timeout:
            print(f"  {r['name']}")
            if r['error']:
                print(f"    Error: {r['error']}")
            print("    → Site is slow or unresponsive")
        print()
    
    # Print other errors
    if errors:
        print("✗ ERROR SITES:")
        print("-" * 70)
        for r in errors:
            print(f"  {r['name']}: {r['status']}")
            if r['error']:
                print(f"    Error: {r['error']}")
        print()
    
    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Total sites tested: {len(results)}")
    print(f"Working: {len(working)}")
    print(f"Zero results (may be filtering): {len(zero_results)}")
    print(f"Blocked: {len(blocked)}")
    print(f"Timeout: {len(timeout)}")
    print(f"Other errors: {len(errors)}")
    print()
    
    if zero_results:
        print("Note: Sites with zero results may be working correctly but")
        print("      returning no matches due to strict search filtering.")
        print("      To verify, manually test these sites with general terms.")
    print()

if __name__ == "__main__":
    main()
