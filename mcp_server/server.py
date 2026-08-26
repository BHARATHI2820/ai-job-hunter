"""
Job Search MCP Server — Phase 7

search_jobs() now deduplicates normalized results before returning.
"""

from typing import TypedDict

from mcp.server import MCPServer

from core.dedup.deduplicate import dedup_jobs
from core.models.normalize import normalize_job
from core.sources.adzuna_source import AdzunaSource
from core.verification.active_check import verify_url_active

mcp = MCPServer("JobSearchServer")

_source = AdzunaSource()


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
        A deduplicated list of normalized job postings.
    """
    raw_jobs = _source.search(role, location)
    normalized = [normalize_job(job) for job in raw_jobs]
    deduped = dedup_jobs(normalized)
    return [job.model_dump(mode="json") for job in deduped]


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