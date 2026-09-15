from core.matching.experience_fit import calculate_experience_fit
from core.models.job import Job


def make_job(
    experience_min: int | None = None,
    experience_max: int | None = None,
) -> Job:
    return Job(
        id="test-1",
        title="Test Job",
        source="test",
        source_job_id="test-1",
        experience_min=experience_min,
        experience_max=experience_max,
    )


def test_candidate_inside_experience_range():
    job = make_job(1, 3)

    score = calculate_experience_fit(job, 1.3)

    assert score == 100.0


def test_candidate_slightly_below_minimum():
    job = make_job(2, 4)

    score = calculate_experience_fit(job, 1.3)

    assert score == 70.0


def test_candidate_far_below_minimum():
    job = make_job(4, 6)

    score = calculate_experience_fit(job, 1.3)

    assert score == 0.0


def test_candidate_above_maximum():
    job = make_job(1, 3)

    score = calculate_experience_fit(job, 5.0)

    assert score == 90.0


def test_open_ended_requirement_candidate_qualifies():
    job = make_job(1, None)

    score = calculate_experience_fit(job, 1.3)

    assert score == 100.0


def test_open_ended_requirement_candidate_does_not_qualify():
    job = make_job(3, None)

    score = calculate_experience_fit(job, 1.3)

    assert score == 0.0


def test_unknown_experience_is_neutral():
    job = make_job()

    score = calculate_experience_fit(job, 1.3)

    assert score == 50.0