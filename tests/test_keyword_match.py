"""
Phase 9 test — uses the real Cognizant description from this project's
own Phase 4 output, including its actual typos ("LangChan", "AgenticAI"),
to honestly demonstrate what exact keyword matching does and doesn't catch.
"""

from core.matching.keyword_match import score_job_against_profile
from core.models.job import Job
from core.profile.candidate_profile import CandidateProfile


def _test_profile() -> CandidateProfile:
    return CandidateProfile(
        genai_llm_skills=["LangChain", "Prompt Engineering", "RAG"],
        backend_skills=["Python"],
        ai_ml_skills=["Machine Learning", "Deep Learning"],
    )


def test_exact_skill_match_found():
    job = Job(
        id="1",
        source="adzuna",
        source_job_id="1",
        title="GEN AI Engineer",
        description="Strong background in machine learning and deep learning, proficiency in Python.",
    )
    matched, score = score_job_against_profile(job, _test_profile())
    assert "Python" in matched
    assert "Machine Learning" in matched
    assert "Deep Learning" in matched
    assert score > 0


def test_typo_in_real_posting_is_not_matched_known_limitation():
    # Real text from this project's own Cognizant Adzuna result (Phase 4)
    job = Job(
        id="2",
        source="adzuna",
        source_job_id="2",
        title="GEN AI Engineer - Cognizant",
        description=(
            "This role requires proficiency in programming languages such as "
            "Python and frameworks like AgenticAI, LangChan, TensorFlow, etc."
        ),
    )
    matched, score = score_job_against_profile(job, _test_profile())
    assert "Python" in matched
    # Documents the known limitation: "LangChan" (typo) does NOT match "LangChain"
    assert "LangChain" not in matched


def test_no_matches_returns_zero_score():
    job = Job(
        id="3",
        source="adzuna",
        source_job_id="3",
        title="Sales Manager",
        description="Looking for someone with strong sales and negotiation skills.",
    )
    matched, score = score_job_against_profile(job, _test_profile())
    assert matched == []
    assert score == 0.0


def test_load_real_profile_from_json():
    from core.profile.load_profile import load_profile

    profile = load_profile()
    all_skills = profile.all_skills()
    assert "LangGraph" in all_skills
    assert "ChromaDB" in all_skills
    assert len(all_skills) > 10