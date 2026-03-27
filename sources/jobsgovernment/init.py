import os

USE_API = os.getenv("JOBSGOVERNMENT_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_jobsgovernment_jobs
else:
    from .scraper import fetch_jobsgovernment_jobs

__all__ = ["fetch_jobsgovernment_jobs"]
