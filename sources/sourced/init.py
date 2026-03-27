import os

USE_API = os.getenv("SOURCED_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_sourced_jobs
else:
    from .scraper import fetch_sourced_jobs

__all__ = ["fetch_sourced_jobs"]
