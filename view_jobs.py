import sqlite3
import pandas as pd
from datetime import datetime
import pytz
import os

conn = sqlite3.connect("jobs.db")

# Get all jobs
df = pd.read_sql_query("""
    SELECT 
        site,
        title,
        company,
        location,
        is_remote,
        job_url,
        first_seen_at
    FROM jobs
    ORDER BY first_seen_at DESC
""", conn)

conn.close()

# Convert is_remote from bytes to boolean
if 'is_remote' in df.columns:
    df['is_remote'] = df['is_remote'].apply(
        lambda x: bool(int.from_bytes(x, byteorder='big')) if isinstance(x, bytes) else bool(x)
    )

# Convert first_seen_at from UTC to Pacific/Auckland timezone
if 'first_seen_at' in df.columns:
    nz_tz = pytz.timezone('Pacific/Auckland')
    df['first_seen_at'] = pd.to_datetime(df['first_seen_at'])
    df['first_seen_at'] = df['first_seen_at'].dt.tz_localize('UTC').dt.tz_convert(nz_tz)
    df['first_seen_at'] = df['first_seen_at'].dt.strftime('%Y-%m-%d %H:%M:%S %Z')

# Filter out jobs with unwanted keywords in title
# Use same environment variable as daily_run.py, or fallback to default
exclude_keywords_str = os.getenv("EXCLUDE_JOB_KEYWORDS", "qa,junior,senior")
exclude_keywords = [
    kw.strip().lower() 
    for kw in exclude_keywords_str.split(",")
    if kw.strip()
]

if 'title' in df.columns and exclude_keywords:
    for keyword in exclude_keywords:
        df = df[~df['title'].str.lower().str.contains(keyword, na=False)]

# Export to CSV
df.to_csv("all_jobs.csv", index=False)
print(f"Exported {len(df)} jobs to all_jobs.csv")

# Show preview
print("\nFirst 10 jobs:")
print(df.head(10).to_string())