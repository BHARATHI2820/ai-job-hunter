"""
Multi-source job search.

Combines results from all configured job sources.
If one source fails, other sources can still return results.
"""
from core.sources.base import JobSource
from core.logging_config import get_logger
logger = get_logger(__name__)

def build_configured_sources(source_classes: list[type[JobSource]]) -> list[JobSource]:
    """
    Instantiate each source class, skipping any that raise ValueError
    (e.g. missing API keys) instead of crashing the whole app.
    """
    sources: list[JobSource] = []

    for source_cls in source_classes:
        try:
            sources.append(source_cls())
        except ValueError as exc:
            logger.warning(
                f"[SOURCE] {source_cls.__name__} not configured, skipping: {exc}"
            )

    if not sources:
        logger.warning("[SOURCE] No job sources are configured!")

    return sources


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