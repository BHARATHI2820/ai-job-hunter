"""
Job freshness scoring — Phase 17.3.

Calculates a deterministic freshness score from a job's posted date.

Recent jobs receive a higher score.
Unknown dates receive a neutral score.
"""

from datetime import datetime, UTC

from core.models.job import Job


UNKNOWN_FRESHNESS_SCORE = 50.0


def calculate_freshness_score(
    job: Job,
    now: datetime | None = None,
) -> float:
    """
    Calculate how fresh a job posting is.

    Scoring:
    - 0–2 days:   100
    - 3–7 days:    90
    - 8–14 days:   75
    - 15–30 days:  50
    - 31–60 days:  30
    - 60+ days:    10
    - Unknown:     50

    `now` can be supplied during tests to avoid depending
    on the actual current time.
    """

    if job.posted_date is None:
        return UNKNOWN_FRESHNESS_SCORE

    if now is None:
        now = datetime.now(UTC)

    posted_date = job.posted_date

    # Make naive datetimes UTC-aware if necessary.
    if posted_date.tzinfo is None:
        posted_date = posted_date.replace(tzinfo=UTC)

    age_days = (now - posted_date).total_seconds() / 86400

    # Future-dated postings are treated as very fresh.
    if age_days <= 2:
        return 100.0

    if age_days <= 7:
        return 90.0

    if age_days <= 14:
        return 75.0

    if age_days <= 30:
        return 50.0

    if age_days <= 60:
        return 30.0

    return 10.0