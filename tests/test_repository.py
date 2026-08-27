"""
Phase 11 test — real integration test against Neon. Skipped if
DATABASE_URL isn't set, same pattern as Phase 4's Adzuna skip guard.
"""

import os

import pytest
from dotenv import load_dotenv
load_dotenv()

from core.models.job import Job

requires_db = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"), reason="DATABASE_URL not set in .env"
)


@requires_db
def test_upsert_job_then_query():
    from db.repository import get_previously_seen_job_ids, upsert_job

    job = Job(
        id="test-1",
        source="test_source",
        source_job_id="test-phase11-001",
        title="Test GenAI Engineer",
        company="TestCo",
        location="Chennai",
    )
    upsert_job(job)

    seen_ids = get_previously_seen_job_ids("test_source")
    assert "test-phase11-001" in seen_ids


@requires_db
def test_save_search_does_not_raise():
    from db.repository import save_search

    save_search("GenAI Engineer", "Chennai", 5)  # just confirm no exception