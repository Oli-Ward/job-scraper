import os

USE_API = os.getenv("TRADEME_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_trademe_jobs
else:
    from .scraper import fetch_trademe_jobs

__all__ = ["fetch_trademe_jobs"]