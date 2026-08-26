"""
Phase 8 test — uses the real Orion Innovation "8 years total" posting
this project actually surfaced during Phase 4-7 testing as the primary
senior-role rejection fixture.
"""

from core.filtering.experience_extractor import extract_experience_range
from core.filtering.hard_filter import HardFilterConfig, apply_hard_filters
from core.models.job import Job


def test_extract_experience_range_total_phrasing():
    # Real description text from the actual Orion Innovation posting
    text = "Role: GenAI Lead Engineer Experience: 8 years total (with significant hands-on GenAI work)"
    exp_min, exp_max = extract_experience_range(text)
    assert exp_min == 8.0
    assert exp_max == 8.0


def test_extract_experience_range_dash_pattern():
    exp_min, exp_max = extract_experience_range("Looking for 1-3 years of experience")
    assert exp_min == 1.0
    assert exp_max == 3.0


def test_extract_experience_range_missing_returns_none():
    exp_min, exp_max = extract_experience_range("Great company culture, remote friendly")
    assert exp_min is None
    assert exp_max is None


def _make_job(**overrides) -> Job:
    defaults = {
        "id": "1",
        "title": "Test Role",
        "company": "TestCo",
        "location": "Chennai, Tamil Nadu",
        "description": "",
        "source": "adzuna",
        "source_job_id": "1",
    }
    defaults.update(overrides)
    return Job(**defaults)


def test_senior_role_is_rejected_real_orion_case():
    job = _make_job(
        title="Gen AI Lead",
        company="Orion Innovation",
        description="Role: GenAI Lead Engineer Experience: 8 years total",
    )
    config = HardFilterConfig(candidate_experience_years=1.3, experience_buffer_years=2.0)
    kept, rejected = apply_hard_filters([job], config)
    assert len(kept) == 0
    assert len(rejected) == 1
    assert "8" in rejected[0][1]


def test_junior_role_within_range_is_kept():
    job = _make_job(description="Looking for 1-3 years of experience in GenAI")
    config = HardFilterConfig(candidate_experience_years=1.3, experience_buffer_years=2.0)
    kept, rejected = apply_hard_filters([job], config)
    assert len(kept) == 1


def test_unknown_experience_is_kept_not_rejected():
    job = _make_job(description="Exciting opportunity, great team culture")
    config = HardFilterConfig(candidate_experience_years=1.3, experience_buffer_years=2.0)
    kept, rejected = apply_hard_filters([job], config)
    assert len(kept) == 1  # unknown must not be treated as "obviously senior"


def test_location_mismatch_is_rejected():
    job = _make_job(location="Bengaluru, Karnataka", description="1-2 years experience")
    config = HardFilterConfig(
        candidate_experience_years=1.3, experience_buffer_years=2.0, requested_location="Chennai"
    )
    kept, rejected = apply_hard_filters([job], config)
    assert len(kept) == 0


def test_remote_is_allowed_regardless_of_requested_city():
    job = _make_job(location="Remote", description="1-2 years experience")
    config = HardFilterConfig(
        candidate_experience_years=1.3,
        experience_buffer_years=2.0,
        requested_location="Chennai",
        allow_remote=True,
    )
    kept, rejected = apply_hard_filters([job], config)
    assert len(kept) == 1