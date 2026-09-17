"""
Adzuna job source — Phase 4.

Uses Adzuna's official public Job Search API (free tier, no scraping,
no anti-bot circumvention). Registered at developer.adzuna.com.
"""

import os

import requests

from core.sources.base import JobSource

from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential
from core.logging_config import get_logger

logger = get_logger(__name__)

def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
        return True
    if isinstance(exc, requests.exceptions.HTTPError):
        status = exc.response.status_code if exc.response is not None else None
        # 429 = rate limit / quota — retrying won't help mid-search, so skip it.
        return status in (500, 502, 503, 504)
    return False


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
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception(_is_retryable),
        reraise=True,
    )
    def _get(self, url: str, params: dict):
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response

    def search(self, role: str, location: str) -> list[dict]:
        url = f"{self.BASE_URL}/{self.country}/search/1"
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": role,
            "where": location,
            "results_per_page": 10,
        }

        try:
            response = self._get(url, params)
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status == 429:
                logger.warning("[ADZUNA] Rate limit / quota hit (429) — skipping this source")
            else:
                logger.warning(f"[ADZUNA] Request failed: {exc}")
            raise
        except requests.exceptions.RequestException as exc:
            logger.warning(f"[ADZUNA] Giving up after retry: {type(exc).__name__}: {exc}")
            raise
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