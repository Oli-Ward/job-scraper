import os

USE_API = os.getenv("CRESCENTCONSULTING_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_crescentconsulting_jobs
else:
    from .scraper import fetch_crescentconsulting_jobs

__all__ = ["fetch_crescentconsulting_jobs"]
