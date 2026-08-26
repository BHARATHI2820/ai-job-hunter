"""
Deduplication — Phase 7.

Two-tier duplicate detection:
1. Exact: same source + same source_job_id (e.g. same API call returned twice)
2. Probable: same company + normalized title + normalized location, but
   different IDs (e.g. a reposted listing, like the real Cognizant example
   this project surfaced during Phase 6 testing).

Per section 13: duplicates are DROPPED, never merged. The first
occurrence in the input order is kept.
"""

import re

from core.models.job import Job


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.strip().lower())


def dedup_jobs(jobs: list[Job]) -> list[Job]:
    seen_exact: set[tuple[str, str]] = set()
    seen_probable: set[tuple[str, str, str]] = set()
    result: list[Job] = []
    removed_count = 0

    for job in jobs:
        exact_key = (job.source, job.source_job_id)
        if exact_key in seen_exact:
            removed_count += 1
            continue
        seen_exact.add(exact_key)

        probable_key = (
            _normalize_text(job.company),
            _normalize_text(job.title),
            _normalize_text(job.location),
        )
        # Only treat as a probable duplicate if all three fields are
        # actually present — an empty/empty/empty key would wrongly
        # collide unrelated jobs with missing data.
        if all(probable_key) and probable_key in seen_probable:
            removed_count += 1
            continue
        if all(probable_key):
            seen_probable.add(probable_key)

        result.append(job)

    if removed_count:
        print(f"[DEDUP] Removed {removed_count} duplicate job(s)")

    return result