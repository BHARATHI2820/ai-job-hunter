"""
Job Search MCP Server — Phase 8

search_jobs() now applies deterministic hard filtering (experience,
location) after dedup, before returning results.
"""

from typing import TypedDict

from mcp.server import MCPServer

from core.dedup.deduplicate import dedup_jobs
from core.filtering.hard_filter import HardFilterConfig, apply_hard_filters
from core.models.normalize import normalize_job
from core.sources.adzuna_source import AdzunaSource
from core.verification.active_check import verify_url_active

mcp = MCPServer("JobSearchServer")

_source = AdzunaSource()

# Configurable, not hardcoded — matches your actual profile (section 2).
# Later phases can move this to an env var or a user-editable profile file.
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
        A deduplicated, hard-filtered list of normalized job postings.
        Jobs requiring significantly more experience than the configured
        candidate profile, or clearly mismatched on location, are excluded.
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