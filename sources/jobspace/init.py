import os

USE_API = os.getenv("JOBSPACE_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_jobspace_jobs
else:
    from .scraper import fetch_jobspace_jobs

__all__ = ["fetch_jobspace_jobs"]
