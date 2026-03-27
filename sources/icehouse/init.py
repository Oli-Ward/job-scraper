import os

USE_API = os.getenv("ICEHOUSE_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_icehouse_jobs
else:
    from .scraper import fetch_icehouse_jobs

__all__ = ["fetch_icehouse_jobs"]
