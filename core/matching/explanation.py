"""
Job match explanation — Phase 16.

Builds a deterministic explanation from existing matching signals.
No LLM call is used.
"""

from core.models.job import Job

def _format_years(value: float | int) -> str:
    """Format experience years without unnecessary decimal zeros."""
    value = float(value)

    if value.is_integer():
        return f"{value:.0f}"

    return f"{value:g}"


def build_match_explanation(job: Job) -> str:
    """Build a human-readable explanation for a job match."""

    parts: list[str] = []

    if job.relevance_score is not None:
        parts.append(
            f"Relevance {job.relevance_score:.1f}/100"
        )

    if job.semantic_match_score is not None:
        parts.append(
            f"Semantic {job.semantic_match_score:.1f}"
        )

    if job.skill_match_score is not None:
        parts.append(
            f"Keyword {job.skill_match_score:.1f}"
        )

    explanation = " — ".join(parts)

    if job.matched_skills:
        skills = ", ".join(job.matched_skills)
        explanation += f". Matched skills: {skills}"

    if job.experience_min is not None:
        if job.experience_max is not None:
            explanation += (
                f". Experience: {_format_years(job.experience_min)}–"
                f"{_format_years(job.experience_max)} years"
            )
        else:
            explanation += (
                f". Experience: {_format_years(job.experience_min)}+ years"
            )

    if job.location:
        explanation += f". Location: {job.location}"

    return explanation + "."