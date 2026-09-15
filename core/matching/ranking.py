"""
Job relevance ranking — Phase 17.2.

Combines semantic matching, keyword/skill matching,
and experience fit into one overall relevance score.
"""

from core.models.job import Job


SEMANTIC_WEIGHT = 0.40
KEYWORD_WEIGHT = 0.35
EXPERIENCE_WEIGHT = 0.25


def calculate_relevance_score(job: Job) -> float:
    """
    Calculate the overall relevance score for a job.

    Weights:
    - Semantic matching: 40%
    - Keyword/skill matching: 35%
    - Experience fit: 25%

    Missing scores are treated as 0.
    """

    semantic_score = job.semantic_match_score or 0.0
    keyword_score = job.skill_match_score or 0.0
    experience_score = job.experience_fit_score or 0.0

    relevance_score = (
        semantic_score * SEMANTIC_WEIGHT
        + keyword_score * KEYWORD_WEIGHT
        + experience_score * EXPERIENCE_WEIGHT
    )

    return round(relevance_score, 1)


def rank_jobs(jobs: list[Job]) -> list[Job]:
    """
    Calculate relevance scores and return jobs
    sorted from highest to lowest relevance.
    """

    for job in jobs:
        job.relevance_score = calculate_relevance_score(job)

    return sorted(
        jobs,
        key=lambda job: job.relevance_score or 0.0,
        reverse=True,
    )