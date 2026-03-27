import os

USE_API = os.getenv("ROBERTHALF_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_roberthalf_jobs
else:
    from .scraper import fetch_roberthalf_jobs

__all__ = ["fetch_roberthalf_jobs"]
