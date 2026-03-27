import os

# Switch between scraper and API based on environment
USE_API = os.getenv("SEEK_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_seek_jobs
else:
    from .scraper import fetch_seek_jobs

__all__ = ["fetch_seek_jobs"]