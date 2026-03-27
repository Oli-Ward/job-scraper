import os

USE_API = os.getenv("DOGOODJOBS_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_dogoodjobs_jobs
else:
    from .scraper import fetch_dogoodjobs_jobs

__all__ = ["fetch_dogoodjobs_jobs"]
