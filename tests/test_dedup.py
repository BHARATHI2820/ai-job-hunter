"""
Phase 7 test — uses the real Cognizant duplicate this project actually
surfaced during Phase 6 testing (two listings, same company/title/location,
different source IDs) as the probable-duplicate fixture.
"""

from core.dedup.deduplicate import dedup_jobs
from core.models.job import Job


def _make_job(**overrides) -> Job:
    defaults = {
        "id": "1",
        "title": "GEN AI Engineer - Cognizant",
        "company": "Cognizant",
        "location": "Chennai, Tamil Nadu",
        "source": "adzuna",
        "source_job_id": "1",
    }
    defaults.update(overrides)
    return Job(**defaults)


def test_exact_duplicate_is_removed():
    job_a = _make_job(source_job_id="5844408611")
    job_b = _make_job(id="5844408611", source_job_id="5844408611")  # same ID again
    result = dedup_jobs([job_a, job_b])
    assert len(result) == 1


def test_probable_duplicate_is_removed_real_cognizant_case():
    # Real example from Phase 6 testing: same role reposted with a new ID
    job_a = _make_job(id="5844408611", source_job_id="5844408611")
    job_b = _make_job(id="5816232615", source_job_id="5816232615")
    result = dedup_jobs([job_a, job_b])
    assert len(result) == 1
    assert result[0].source_job_id == "5844408611"  # first occurrence kept


def test_different_companies_same_title_are_not_merged():
    job_a = _make_job(id="1", source_job_id="1", company="Cognizant")
    job_b = _make_job(id="2", source_job_id="2", company="Deloitte")
    result = dedup_jobs([job_a, job_b])
    assert len(result) == 2  # genuinely different jobs, must NOT collide


def test_jobs_with_missing_fields_do_not_false_collide():
    job_a = _make_job(id="1", source_job_id="1", company=None, title="Role A")
    job_b = _make_job(id="2", source_job_id="2", company=None, title="Role B")
    result = dedup_jobs([job_a, job_b])
    assert len(result) == 2