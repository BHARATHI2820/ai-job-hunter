from datetime import datetime, timedelta, UTC

from core.matching.freshness import calculate_freshness_score
from core.models.job import Job


def make_job(posted_date=None):
    return Job(
        id="test-1",
        title="Test Job",
        source="test",
        source_job_id="test-1",
        posted_date=posted_date,
    )


def test_unknown_posted_date_is_neutral():
    job = make_job()

    score = calculate_freshness_score(job)

    assert score == 50.0


def test_job_posted_today_is_very_fresh():
    now = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
    job = make_job(now)

    score = calculate_freshness_score(job, now)

    assert score == 100.0


def test_job_posted_two_days_ago_is_very_fresh():
    now = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
    posted = now - timedelta(days=2)

    job = make_job(posted)

    score = calculate_freshness_score(job, now)

    assert score == 100.0


def test_job_posted_one_week_ago():
    now = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
    posted = now - timedelta(days=7)

    job = make_job(posted)

    score = calculate_freshness_score(job, now)

    assert score == 90.0


def test_job_posted_two_weeks_ago():
    now = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
    posted = now - timedelta(days=14)

    job = make_job(posted)

    score = calculate_freshness_score(job, now)

    assert score == 75.0


def test_job_posted_one_month_ago():
    now = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
    posted = now - timedelta(days=30)

    job = make_job(posted)

    score = calculate_freshness_score(job, now)

    assert score == 50.0


def test_job_posted_two_months_ago():
    now = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
    posted = now - timedelta(days=60)

    job = make_job(posted)

    score = calculate_freshness_score(job, now)

    assert score == 30.0


def test_old_job_gets_low_score():
    now = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
    posted = now - timedelta(days=61)

    job = make_job(posted)

    score = calculate_freshness_score(job, now)

    assert score == 10.0


def test_future_posted_date_is_treated_as_fresh():
    now = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
    posted = now + timedelta(days=1)

    job = make_job(posted)

    score = calculate_freshness_score(job, now)

    assert score == 100.0