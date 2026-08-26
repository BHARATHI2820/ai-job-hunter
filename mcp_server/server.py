"""
Job Search MCP Server — Phase 6

Now exposes two tools: search_jobs() and verify_job_active().
Gemini decides when each is needed; the server has no opinion.
"""

from mcp.server import MCPServer
from typing import TypedDict

from core.models.normalize import normalize_job
from core.sources.adzuna_source import AdzunaSource
from core.verification.active_check import verify_url_active

class ActiveCheckResult(TypedDict):
    active_status: str
    active_status_reason: str

mcp = MCPServer("JobSearchServer")

_source = AdzunaSource()


@mcp.tool()
def search_jobs(role: str, location: str) -> list[dict]:
    """Search for jobs matching a role and location.

    Args:
        role: Job title or role to search for, e.g. "GenAI Engineer".
        location: City or "Remote", e.g. "Chennai".

    Returns:
        A list of normalized job postings matching the search criteria.
    """
    raw_jobs = _source.search(role, location)
    normalized = [normalize_job(job) for job in raw_jobs]
    return [job.model_dump(mode="json") for job in normalized]


@mcp.tool()
def verify_job_active(job_url: str) -> ActiveCheckResult:
    """Check whether a job posting's application page is currently reachable.

    Args:
        job_url: The direct URL to the job posting.

    Returns:
        A dict with active_status ("active"/"inactive"/"unknown") and
        active_status_reason explaining the result. This is a best-effort
        signal, not a guarantee the posting is still accepting applications.
    """
    return verify_url_active(job_url)


if __name__ == "__main__":
    mcp.run()