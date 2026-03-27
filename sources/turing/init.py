import os

USE_API = os.getenv("TURING_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_turing_jobs
else:
    from .scraper import fetch_turing_jobs

__all__ = ["fetch_turing_jobs"]
