from core.matching.ranking import calculate_relevance_score, rank_jobs
from core.models.job import Job


def make_job(
    semantic_score=None,
    keyword_score=None,
    experience_score=None,
):
    return Job(
        id="test-1",
        title="Test Job",
        source="test",
        source_job_id="test-1",
        semantic_match_score=semantic_score,
        skill_match_score=keyword_score,
        experience_fit_score=experience_score,
    )


def test_relevance_score_formula():
    job = make_job(
        semantic_score=70.0,
        keyword_score=60.0,
        experience_score=100.0,
    )

    score = calculate_relevance_score(job)

    # 70 * 0.40 + 60 * 0.35 + 100 * 0.25
    # = 28 + 21 + 25 = 74
    assert score == 74.0


def test_rank_jobs_descending():
    job1 = make_job(
        semantic_score=80.0,
        keyword_score=70.0,
        experience_score=100.0,
    )

    job2 = make_job(
        semantic_score=50.0,
        keyword_score=40.0,
        experience_score=70.0,
    )

    ranked = rank_jobs([job2, job1])

    assert ranked[0] is job1
    assert ranked[1] is job2
    assert ranked[0].relevance_score > ranked[1].relevance_score


def test_missing_scores_treated_as_zero():
    job = make_job()

    score = calculate_relevance_score(job)

    assert score == 0.0


def test_experience_fit_affects_relevance_score():
    job_without_experience_fit = make_job(
        semantic_score=70.0,
        keyword_score=60.0,
        experience_score=0.0,
    )

    job_with_experience_fit = make_job(
        semantic_score=70.0,
        keyword_score=60.0,
        experience_score=100.0,
    )

    score_without = calculate_relevance_score(
        job_without_experience_fit
    )
    score_with = calculate_relevance_score(
        job_with_experience_fit
    )

    assert score_with > score_without
    assert score_with == 74.0
    assert score_without == 49.0