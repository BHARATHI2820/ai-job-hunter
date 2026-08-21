"""
Job Search MCP Server — Phase 4

search_jobs() now calls a real JobSource (Adzuna) instead of returning
mock data. The MCP protocol layer is completely unchanged from Phase 2.
"""

from mcp.server import MCPServer

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
        A list of job postings matching the search criteria.
    """
    return _source.search(role, location)


if __name__ == "__main__":
    mcp.run()