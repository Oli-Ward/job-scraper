import os

USE_API = os.getenv("YOUNITY_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_younity_jobs
else:
    from .scraper import fetch_younity_jobs

__all__ = ["fetch_younity_jobs"]
