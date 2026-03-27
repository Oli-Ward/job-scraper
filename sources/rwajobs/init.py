import os

USE_API = os.getenv("RWAJOBS_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_rwajobs_jobs
else:
    from .scraper import fetch_rwajobs_jobs

__all__ = ["fetch_rwajobs_jobs"]
