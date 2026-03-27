import os

USE_API = os.getenv("MATCHSTIQ_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_matchstiq_jobs
else:
    from .scraper import fetch_matchstiq_jobs

__all__ = ["fetch_matchstiq_jobs"]
