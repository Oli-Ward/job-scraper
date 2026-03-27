import os

USE_API = os.getenv("TRIBE_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_tribe_jobs
else:
    from .scraper import fetch_tribe_jobs

__all__ = ["fetch_tribe_jobs"]
