import os

USE_API = os.getenv("RECRUITIT_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_recruitit_jobs
else:
    from .scraper import fetch_recruitit_jobs

__all__ = ["fetch_recruitit_jobs"]
