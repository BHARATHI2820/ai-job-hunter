"""
Adzuna job source — Phase 4.

Uses Adzuna's official public Job Search API (free tier, no scraping,
no anti-bot circumvention). Registered at developer.adzuna.com.
"""

import os

import requests

from core.sources.base import JobSource


class AdzunaSource(JobSource):
    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    def __init__(self) -> None:
        self.app_id = os.getenv("ADZUNA_APP_ID")
        self.app_key = os.getenv("ADZUNA_APP_KEY")
        self.country = os.getenv("ADZUNA_COUNTRY", "in")

        if not self.app_id or not self.app_key:
            raise ValueError(
                "ADZUNA_APP_ID and ADZUNA_APP_KEY must be set in .env"
            )

    def search(self, role: str, location: str) -> list[dict]:
        url = f"{self.BASE_URL}/{self.country}/search/1"
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": role,
            "where": location,
            "results_per_page": 10,
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        raw_results = response.json().get("results", [])

        # Map Adzuna's field names into our own shape.
        # This is the ONLY place that knows Adzuna's response format.
        jobs = []
        for job in raw_results:
            jobs.append(
                {
                    "id": job.get("id"),
                    "title": job.get("title"),
                    "company": job.get("company", {}).get("display_name"),
                    "location": job.get("location", {}).get("display_name"),
                    "description": job.get("description"),
                    "salary_min": job.get("salary_min"),
                    "salary_max": job.get("salary_max"),
                    "posted_date": job.get("created"),
                    "job_url": job.get("redirect_url"),
                    "source": "adzuna",
                    "active_status": "unknown",
                    "active_status_reason": "Not yet verified (Phase 6 will add verification)",
                }
            )
        return jobs