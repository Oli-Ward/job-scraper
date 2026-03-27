import os

USE_API = os.getenv("JOBTED_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_jobted_jobs
else:
    from .scraper import fetch_jobted_jobs

__all__ = ["fetch_jobted_jobs"]
