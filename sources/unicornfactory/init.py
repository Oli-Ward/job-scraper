import os

USE_API = os.getenv("UNICORNFACTORY_USE_API", "false").lower() == "true"

if USE_API:
    from .api import fetch_unicornfactory_jobs
else:
    from .scraper import fetch_unicornfactory_jobs

__all__ = ["fetch_unicornfactory_jobs"]
