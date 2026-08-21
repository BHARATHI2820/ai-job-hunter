"""
Phase 5 test — validates normalization handles both clean and messy
real-world data (missing fields, malformed dates) without crashing.
"""

from core.models.job import Job
from core.models.normalize import normalize_job


def test_normalize_job_with_complete_data():
    raw = {
        "id": "12345",
        "title": "GenAI Engineer",
        "company": "TestCorp",
        "location": "Chennai, Tamil Nadu",
        "salary_min": 1000000,
        "salary_max": 1500000,
        "source": "adzuna",
        "job_url": "https://example.com/job/12345",
        "posted_date": "2026-08-15T16:04:16Z",
        "active_status": "unknown",
    }
    job = normalize_job(raw)
    assert isinstance(job, Job)
    assert job.title == "GenAI Engineer"
    assert job.posted_date is not None
    assert job.currency == "INR"


def test_normalize_job_with_missing_fields():
    raw = {"id": "99999", "source": "adzuna"}
    job = normalize_job(raw)
    assert job.title == "Untitled"
    assert job.company is None
    assert job.posted_date is None
    assert job.active_status == "unknown"


def test_normalize_job_with_malformed_date():
    raw = {"id": "11111", "title": "Test Role", "source": "adzuna", "posted_date": "not-a-date"}
    job = normalize_job(raw)
    assert job.posted_date is None  # should not crash, should degrade gracefully