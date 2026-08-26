"""
Phase 10 test — uses the real Cognizant description (containing the
"LangChan" typo) from this project's own live data. The core claim to
prove: semantic matching scores this job meaningfully higher than an
unrelated job, even though keyword matching (Phase 9) scored it low.
"""

from core.matching.semantic_match import build_profile_text, semantic_score_jobs
from core.models.job import Job
from core.profile.candidate_profile import CandidateProfile


def _test_profile() -> CandidateProfile:
    return CandidateProfile(
        genai_llm_skills=["LLM", "Generative AI", "RAG", "LangChain", "Prompt Engineering"],
        backend_skills=["Python"],
        ai_ml_skills=["Machine Learning", "Deep Learning"],
    )


def test_build_profile_text_includes_skills():
    text = build_profile_text(_test_profile())
    assert "LangChain" in text
    assert "Python" in text


def test_relevant_job_scores_higher_than_unrelated_job_real_cognizant_case():
    genai_job = Job(
        id="1",
        source="adzuna",
        source_job_id="1",
        title="GEN AI Engineer - Cognizant",
        # Real text from this project's own Phase 4 Adzuna result, typo included
        description=(
            "We are seeking a highly skilled and motivated GenAI and Machine "
            "Learning Engineer. Strong background in machine learning and deep "
            "learning, hands-on experience developing generative AI models. "
            "Proficiency in Python and frameworks like AgenticAI, LangChan, TensorFlow."
        ),
    )
    unrelated_job = Job(
        id="2",
        source="adzuna",
        source_job_id="2",
        title="Sales Manager",
        description="Looking for someone with strong sales, negotiation, and client relationship skills.",
    )

    jobs = [genai_job, unrelated_job]
    semantic_score_jobs(jobs, _test_profile())

    assert genai_job.semantic_match_score is not None
    assert unrelated_job.semantic_match_score is not None
    assert genai_job.semantic_match_score > unrelated_job.semantic_match_score


def test_semantic_score_present_even_when_keyword_typo_exists():
    # Demonstrates the actual Phase 9 gap being closed: keyword matching
    # missed "LangChan", but semantic matching should still recognize
    # this job as strongly GenAI-relevant.
    job = Job(
        id="3",
        source="adzuna",
        source_job_id="3",
        title="GEN AI Engineer",
        description="Frameworks like AgenticAI, LangChan, TensorFlow for generative AI development.",
    )
    semantic_score_jobs([job], _test_profile())
    assert job.semantic_match_score is not None
    assert job.semantic_match_score > 0