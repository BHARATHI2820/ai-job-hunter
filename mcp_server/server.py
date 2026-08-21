"""
Job Search MCP Server — Phase 5

search_jobs() now normalizes every raw result into a validated Job
model before returning. MCP protocol layer itself is unchanged.
"""

from mcp.server import MCPServer

from core.models.normalize import normalize_job
from core.sources.adzuna_source import AdzunaSource

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


if __name__ == "__main__":
    mcp.run()