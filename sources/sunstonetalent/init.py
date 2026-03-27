import os

USE_API = os.getenv("SUNSTONETALENT_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_sunstonetalent_jobs
else:
    from .scraper import fetch_sunstonetalent_jobs

__all__ = ["fetch_sunstonetalent_jobs"]
