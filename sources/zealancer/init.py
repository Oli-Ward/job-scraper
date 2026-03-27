import os

USE_API = os.getenv("ZEALANCER_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_zealancer_jobs
else:
    from .scraper import fetch_zealancer_jobs

__all__ = ["fetch_zealancer_jobs"]
