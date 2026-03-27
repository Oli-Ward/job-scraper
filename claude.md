# Job Scraper Project

A Python-based job aggregation tool that scrapes tech job listings from multiple sources in New Zealand.

## Overview

This project automatically collects software engineering and developer job postings from various job boards, stores them in a SQLite database, and provides tools for viewing and exporting the data. It's designed to run daily and track new job postings over time.

## Project Structure

```
job-scraper/
├── daily_run.py           # Main entry point - orchestrates job fetching
├── view_jobs.py           # Exports jobs to CSV and displays preview
├── requirements.txt       # Python dependencies
├── jobs.db               # SQLite database (created on first run)
├── all_jobs.csv          # Exported jobs (created by view_jobs.py)
├── .env                  # Environment configuration
├── sources/              # Job source implementations
│   ├── jobspy_source.py  # JobSpy API wrapper (Indeed, LinkedIn, Google)
│   ├── seek/             # Seek.co.nz scraper
│   │   ├── init.py       # Source selector (API vs scraper)
│   │   ├── scraper.py    # HTML scraper implementation
│   │   └── api.py        # API implementation (future)
│   └── trademe/          # Trade Me Jobs scraper
│       ├── init.py       # Source selector (API vs scraper)
│       ├── scraper.py    # HTML scraper implementation
│       └── api.py        # API implementation (future)
└── storage/              # Data persistence layer
    └── sqlite.py         # Database operations
```

## Data Sources

### 1. JobSpy (jobspy_source.py)
- Uses the `python-jobspy` library to fetch jobs from:
  - Indeed
  - LinkedIn
  - Google Jobs
- Configured for:
  - Tech stack: React, TypeScript, JavaScript, Node.js
  - Location: New Zealand
  - Remote jobs only
  - Last 24 hours
  - Up to 50 results per run

### 2. Seek (sources/seek/)
- Custom HTML scraper for Seek.co.nz
- Searches ICT category (classification 6281)
- Keywords: "react typescript javascript node"
- Location: New Zealand
- Can switch to API mode via `SEEK_USE_API=true` environment variable

### 3. Trade Me Jobs (sources/trademe/)
- Custom HTML scraper for Trade Me Jobs
- Can switch to API mode via `TRADEME_USE_API=true` environment variable

## Database Schema

The `jobs` table stores all job listings:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key (auto-increment) |
| site | TEXT | Source site (e.g., "indeed", "seek", "trademe") |
| title | TEXT | Job title |
| company | TEXT | Company name |
| location | TEXT | Job location |
| is_remote | BOOLEAN | Whether job is remote |
| job_url | TEXT | Direct link to job posting (UNIQUE) |
| date_posted | TEXT | When the job was posted |
| description | TEXT | Job description |
| first_seen_at | TEXT | Timestamp when first scraped (auto-generated) |

Duplicate jobs are prevented via the UNIQUE constraint on `job_url`.

## Usage

### Daily Job Collection

Run the main scraper:
```bash
python daily_run.py
```

This will:
1. Initialize the database if it doesn't exist
2. Fetch jobs from all sources
3. Combine and deduplicate results
4. Insert new jobs into the database
5. Print the count of newly inserted jobs

### View and Export Jobs

Export all jobs to CSV and view a preview:
```bash
python view_jobs.py
```

This creates `all_jobs.csv` with all jobs from the database, ordered by most recent first.

## Environment Variables

Configure in `.env` file:

```bash
# Switch sources from HTML scrapers to API implementations
SEEK_USE_API=false        # Set to 'true' to use Seek API
TRADEME_USE_API=false     # Set to 'true' to use Trade Me API
```

## Dependencies

Main dependencies (see requirements.txt):
- `python-jobspy>=1.1.0` - JobSpy API client
- `pandas` - Data manipulation
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `requests-oauthlib` - OAuth for Trade Me API (future use)

Install with:
```bash
pip install -r requirements.txt
```

## Architecture Decisions

### Modular Source Design
Each job source (Seek, Trade Me) has:
- `init.py` - Switches between scraper and API based on environment
- `scraper.py` - HTML parsing implementation
- `api.py` - Official API implementation (for when credentials are available)

This allows easy switching between scraping and API modes without code changes.

### Deduplication Strategy
- URLs are used as unique identifiers
- Deduplication happens at two levels:
  1. In-memory: Before database insertion (daily_run.py:17)
  2. Database: UNIQUE constraint on job_url column

### Data Normalization
Each source returns a standardized DataFrame with columns:
- site, title, company, location, is_remote, job_url, date_posted, description

This ensures consistent data structure regardless of source.

## Development Notes

### HTML Scraping Considerations
- Seek scraper uses CSS selectors for job cards (sources/seek/scraper.py:44-48)
- Includes fallback selectors if site structure changes
- User-Agent headers mimic real browsers to avoid blocking
- Rate limiting with 1-second delays between requests

### Search Focus
Optimized for:
- Tech roles: Software Engineer, Software Developer, Full Stack
- Tech stack: React, TypeScript, JavaScript, Node.js
- Location: New Zealand
- Recency: Last 24 hours

## Future Enhancements

1. Implement Seek API integration (api.py exists but needs credentials)
2. Implement Trade Me API integration (requires OAuth setup)
3. Add email notifications for new jobs matching specific criteria
4. Add job filtering UI
5. Add job description analysis/categorization
6. Add scheduled runs via cron or similar
7. Add logging for debugging and monitoring
8. Add tests

## Maintenance

### Updating Search Criteria
- JobSpy query: Modify `TECH_QUERY` in sources/jobspy_source.py:4-7
- Seek keywords: Modify `KEYWORDS` in sources/seek/scraper.py:8
- Trade Me keywords: Update in sources/trademe/scraper.py

### Database Management
Reset database (deletes all jobs):
```bash
rm jobs.db
python daily_run.py  # Will recreate
```

## Troubleshooting

### No jobs found
- Check internet connection
- Verify search terms aren't too restrictive
- Check if job sites have changed their HTML structure
- Enable verbose output in scraper files

### Duplicate jobs still appearing
- The UNIQUE constraint should prevent this
- Check if job URLs are being normalized consistently
- Verify job_url field isn't None/empty

### Scraper errors
- Job sites may have updated their HTML structure
- Update CSS selectors in scraper.py files
- Consider switching to API mode if available
