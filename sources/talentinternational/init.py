import os

USE_API = os.getenv("TALENTINTERNATIONAL_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_talentinternational_jobs
else:
    from .scraper import fetch_talentinternational_jobs

__all__ = ["fetch_talentinternational_jobs"]
