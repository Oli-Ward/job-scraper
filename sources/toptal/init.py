import os

USE_API = os.getenv("TOPTAL_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_toptal_jobs
else:
    from .scraper import fetch_toptal_jobs

__all__ = ["fetch_toptal_jobs"]
