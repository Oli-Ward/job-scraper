import os

USE_API = os.getenv("ROBERTWALTERS_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_robertwalters_jobs
else:
    from .scraper import fetch_robertwalters_jobs

__all__ = ["fetch_robertwalters_jobs"]
