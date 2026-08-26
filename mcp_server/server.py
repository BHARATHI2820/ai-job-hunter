"""
Job Search MCP Server — Phase 10

search_jobs() now also computes a semantic_match_score for each job,
using embeddings to catch meaning-level fit that exact keyword
matching (Phase 9) misses.
"""

from typing import TypedDict

from mcp.server import MCPServer

from core.dedup.deduplicate import dedup_jobs
from core.filtering.hard_filter import HardFilterConfig, apply_hard_filters
from core.matching.keyword_match import score_job_against_profile
from core.matching.semantic_match import semantic_score_jobs
from core.models.normalize import normalize_job
from core.profile.load_profile import load_profile
from core.sources.adzuna_source import AdzunaSource
from core.verification.active_check import verify_url_active

mcp = MCPServer("JobSearchServer")

_source = AdzunaSource()
_profile = load_profile()

_FILTER_CONFIG = HardFilterConfig(
    candidate_experience_years=1.3,
    experience_buffer_years=2.0,
    allow_remote=True,
)


class ActiveCheckResult(TypedDict):
    active_status: str
    active_status_reason: str


@mcp.tool()
def search_jobs(role: str, location: str) -> list[dict]:
    """Search for jobs matching a role and location.

    Args:
        role: Job title or role to search for, e.g. "GenAI Engineer".
        location: City or "Remote", e.g. "Chennai".

    Returns:
        A deduplicated, hard-filtered list of jobs, each scored two ways:
        skill_match_score (exact keyword overlap) and semantic_match_score
        (embedding-based meaning similarity, catches paraphrased or
        misspelled skills that keyword matching misses).
    """
    raw_jobs = _source.search(role, location)
    normalized = [normalize_job(job) for job in raw_jobs]
    deduped = dedup_jobs(normalized)

    config = HardFilterConfig(
        candidate_experience_years=_FILTER_CONFIG.candidate_experience_years,
        experience_buffer_years=_FILTER_CONFIG.experience_buffer_years,
        requested_location=location,
        allow_remote=_FILTER_CONFIG.allow_remote,
    )
    kept, _rejected = apply_hard_filters(deduped, config)

    for job in kept:
        matched, score = score_job_against_profile(job, _profile)
        job.matched_skills = matched
        job.skill_match_score = score

    semantic_score_jobs(kept, _profile)

    return [job.model_dump(mode="json") for job in kept]


@mcp.tool()
def verify_job_active(job_url: str) -> ActiveCheckResult:
    """Check whether a job posting's application page is currently reachable.

    Args:
        job_url: The direct URL to the job posting.

    Returns:
        A dict with active_status ("active"/"inactive"/"unknown") and
        active_status_reason. Best-effort signal, not a guarantee.
    """
    return verify_url_active(job_url)


if __name__ == "__main__":
    mcp.run()