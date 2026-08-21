"""
Normalization logic — Phase 5.

Converts a raw source dict (already loosely mapped by the source's own
adapter, e.g. AdzunaSource) into a validated Job model.
"""

from datetime import datetime

from core.models.job import Job


def normalize_job(raw: dict) -> Job:
    posted_date = None
    if raw.get("posted_date"):
        try:
            posted_date = datetime.fromisoformat(
                raw["posted_date"].replace("Z", "+00:00")
            )
        except (ValueError, AttributeError):
            posted_date = None

    return Job(
        id=str(raw.get("id")),
        title=raw.get("title") or "Untitled",
        company=raw.get("company"),
        location=raw.get("location"),
        description=raw.get("description"),
        salary_min=raw.get("salary_min"),
        salary_max=raw.get("salary_max"),
        source=raw.get("source", "unknown"),
        source_job_id=str(raw.get("id")),
        job_url=raw.get("job_url"),
        posted_date=posted_date,
        active_status=raw.get("active_status", "unknown"),
        active_status_reason=raw.get("active_status_reason"),
    )