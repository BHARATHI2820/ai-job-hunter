from core.matching.explanation import build_match_explanation
from core.models.job import Job


def make_job() -> Job:
    return Job(
        id="1",
        title="GenAI Engineer",
        source="test",
        source_job_id="1",
        company="TestCorp",
        location="Chennai",
        matched_skills=["Python", "GenAI", "RAG"],
        skill_match_score=75.0,
        semantic_match_score=80.0,
        relevance_score=78.0,
        experience_min=1,
        experience_max=3,
    )


def test_build_match_explanation_contains_matching_signals():
    job = make_job()

    explanation = build_match_explanation(job)

    assert "Relevance 78.0/100" in explanation
    assert "Semantic 80.0" in explanation
    assert "Keyword 75.0" in explanation
    assert "Matched skills: Python, GenAI, RAG" in explanation
    assert "Experience: 1–3 years" in explanation
    assert "Location: Chennai" in explanation


def test_build_match_explanation_without_optional_scores():
    job = Job(
        id="2",
        title="Python Developer",
        source="test",
        source_job_id="2",
    )

    explanation = build_match_explanation(job)

    assert explanation == "."


def test_build_match_explanation_with_min_experience_only():
    job = Job(
        id="3",
        title="AI Engineer",
        source="test",
        source_job_id="3",
        experience_min=2,
        location="Remote",
    )

    explanation = build_match_explanation(job)

    assert "Experience: 2+ years" in explanation
    assert "Location: Remote" in explanation