from core.matching.ranking import calculate_relevance_score, rank_jobs
from core.models.job import Job


def make_job(
    job_id: str,
    skill_score: float | None,
    semantic_score: float | None,
) -> Job:
    return Job(
        id=job_id,
        title=f"Job {job_id}",
        source="test",
        source_job_id=job_id,
        skill_match_score=skill_score,
        semantic_match_score=semantic_score,
    )


def test_calculate_relevance_score():
    job = make_job(
        "1",
        skill_score=80.0,
        semantic_score=70.0,
    )

    score = calculate_relevance_score(job)

    assert score == 74.0


def test_rank_jobs_highest_first():
    job1 = make_job("1", 80.0, 70.0)  # 74.0
    job2 = make_job("2", 60.0, 90.0)  # 78.0
    job3 = make_job("3", 50.0, 50.0)  # 50.0

    ranked = rank_jobs([job1, job2, job3])

    assert [job.id for job in ranked] == ["2", "1", "3"]

    assert ranked[0].relevance_score == 78.0
    assert ranked[1].relevance_score == 74.0
    assert ranked[2].relevance_score == 50.0


def test_missing_scores_are_treated_as_zero():
    job = make_job(
        "1",
        skill_score=None,
        semantic_score=80.0,
    )

    score = calculate_relevance_score(job)

    assert score == 48.0