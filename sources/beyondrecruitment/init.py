import os

USE_API = os.getenv("BEYONDRECRUITMENT_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_beyondrecruitment_jobs
else:
    from .scraper import fetch_beyondrecruitment_jobs

__all__ = ["fetch_beyondrecruitment_jobs"]
