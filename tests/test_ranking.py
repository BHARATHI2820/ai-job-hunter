from core.matching.ranking import calculate_relevance_score, rank_jobs
from core.models.job import Job


def make_job(
    semantic_score=None,
    keyword_score=None,
    experience_score=None,
    freshness_score=None,
):
    return Job(
        id="test-1",
        title="Test Job",
        source="test",
        source_job_id="test-1",
        semantic_match_score=semantic_score,
        skill_match_score=keyword_score,
        experience_fit_score=experience_score,
        freshness_score=freshness_score,
    )


def test_relevance_score_formula():
    job = make_job(
        semantic_score=70.0,
        keyword_score=60.0,
        experience_score=100.0,
        freshness_score=100.0,
    )

    score = calculate_relevance_score(job)

    # 70 * 0.35 + 60 * 0.30 + 100 * 0.25 + 100 * 0.10
    # = 24.5 + 18 + 25 + 10
    # = 77.5
    assert score == 77.5


def test_rank_jobs_descending():
    job1 = make_job(
        semantic_score=80.0,
        keyword_score=70.0,
        experience_score=100.0,
        freshness_score=100.0,
    )

    job2 = make_job(
        semantic_score=50.0,
        keyword_score=40.0,
        experience_score=70.0,
        freshness_score=30.0,
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
        freshness_score=100.0,
    )

    job_with_experience_fit = make_job(
        semantic_score=70.0,
        keyword_score=60.0,
        experience_score=100.0,
        freshness_score=100.0,
    )

    score_without = calculate_relevance_score(
        job_without_experience_fit
    )
    score_with = calculate_relevance_score(
        job_with_experience_fit
    )

    assert score_with > score_without
    assert score_with == 77.5
    assert score_without == 52.5


def test_freshness_affects_relevance_score():
    old_job = make_job(
        semantic_score=70.0,
        keyword_score=60.0,
        experience_score=100.0,
        freshness_score=30.0,
    )

    fresh_job = make_job(
        semantic_score=70.0,
        keyword_score=60.0,
        experience_score=100.0,
        freshness_score=100.0,
    )

    old_score = calculate_relevance_score(old_job)
    fresh_score = calculate_relevance_score(fresh_job)

    assert fresh_score > old_score
    assert fresh_score == 77.5
    assert old_score == 70.5