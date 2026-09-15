"""
Multi-source job search.

Combines results from all configured job sources.
If one source fails, other sources can still return results.
"""
from core.sources.base import JobSource
from core.logging_config import get_logger
logger = get_logger(__name__)


class MultiSourceJobSource(JobSource):
    def __init__(self, sources: list[JobSource]) -> None:
        self.sources = sources

    def search(self, role: str, location: str) -> list[dict]:
        all_jobs: list[dict] = []

        for source in self.sources:
            try:
                jobs = source.search(role, location)
                all_jobs.extend(jobs)

                logger.info(
                    f"[SOURCE] {source.__class__.__name__} "
                    f"returned {len(jobs)} job(s)"
                )

            except Exception as exc:
                logger.warning(
                    f"[SOURCE] {source.__class__.__name__} failed: "
                    f"{type(exc).__name__}: {exc} — skipped"
                )

        return all_jobs