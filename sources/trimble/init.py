import os

USE_API = os.getenv("TRIMBLE_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_trimble_jobs
else:
    from .scraper import fetch_trimble_jobs

__all__ = ["fetch_trimble_jobs"]
