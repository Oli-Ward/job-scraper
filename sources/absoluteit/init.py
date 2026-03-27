import os

USE_API = os.getenv("ABSOLUTEIT_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_absoluteit_jobs
else:
    from .scraper import fetch_absoluteit_jobs

__all__ = ["fetch_absoluteit_jobs"]
