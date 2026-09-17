"""
IndianAPI Jobs source.

Uses IndianAPI's Jobs API to fetch job postings.
The API-specific response format is mapped into our common raw-job shape.
"""

import os

import requests
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from core.logging_config import get_logger
from core.sources.base import JobSource

logger = get_logger(__name__)


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
        return True
    if isinstance(exc, requests.exceptions.HTTPError):
        status = exc.response.status_code if exc.response is not None else None
        return status in (500, 502, 503, 504)
    return False


class IndianAPISource(JobSource):
    BASE_URL = "https://jobs.indianapi.in/jobs"

    def __init__(self) -> None:
        self.api_key = os.getenv("INDIANAPI_JOBS_API_KEY")

        if not self.api_key:
            raise ValueError(
                "INDIANAPI_JOBS_API_KEY must be set in .env"
            )

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception(_is_retryable),
        reraise=True,
    )
    def _get(self, headers: dict, params: dict):
        response = requests.get(
            self.BASE_URL,
            headers=headers,
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        return response

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

        try:
            response = self._get(headers, params)
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status == 429:
                logger.warning("[INDIANAPI] Quota exhausted (429) — skipping this source")
            else:
                logger.warning(f"[INDIANAPI] Request failed: {exc}")
            raise
        except requests.exceptions.RequestException as exc:
            logger.warning(f"[INDIANAPI] Giving up after retry: {type(exc).__name__}: {exc}")
            raise

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