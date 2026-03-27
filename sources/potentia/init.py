import os

USE_API = os.getenv("POTENTIA_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_potentia_jobs
else:
    from .scraper import fetch_potentia_jobs

__all__ = ["fetch_potentia_jobs"]
