"""
IndianAPI Jobs source.

Uses IndianAPI's Jobs API to fetch job postings.
The API-specific response format is mapped into our common raw-job shape.
"""

import os

import requests

from core.sources.base import JobSource


class IndianAPISource(JobSource):
    BASE_URL = "https://jobs.indianapi.in/jobs"

    def __init__(self) -> None:
        self.api_key = os.getenv("INDIANAPI_JOBS_API_KEY")

        if not self.api_key:
            raise ValueError(
                "INDIANAPI_JOBS_API_KEY must be set in .env"
            )

    def search(self, role: str, location: str) -> list[dict]:
        headers = {
            "x-api-key": self.api_key,
            "accept": "application/json",
        }

        params = {
            "title": role,
            "location": location,
            "limit": 10,
        }

        response = requests.get(
            self.BASE_URL,
            headers=headers,
            params=params,
            timeout=15,
        )
        response.raise_for_status()

        raw_results = response.json()

        if not isinstance(raw_results, list):
            return []

        jobs = []

        for job in raw_results:
            jobs.append(
                {
                    "id": job.get("id"),
                    "title": job.get("title") or job.get("job_title"),
                    "company": job.get("company"),
                    "location": job.get("location"),
                    "description": (
                        job.get("job_description")
                        or ""
                    ),
                    "experience": job.get("experience"),
                    "salary_min": None,
                    "salary_max": None,
                    "posted_date": job.get("posted_date"),
                    "job_url": job.get("apply_link"),
                    "source": "indianapi",
                    "active_status": "unknown",
                    "active_status_reason": (
                        "Not yet verified"
                    ),
                }
            )

        return jobs