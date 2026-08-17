"""
Job Search MCP Server — Phase 2

Exposes a single mock tool: search_jobs().
No real job source, no LLM, no client logic here — server only.
"""

from mcp.server import MCPServer

mcp = MCPServer("JobSearchServer")


@mcp.tool()
def search_jobs(role: str, location: str) -> list[dict]:
    """Search for jobs matching a role and location.

    Args:
        role: Job title or role to search for, e.g. "GenAI Engineer".
        location: City or "Remote", e.g. "Chennai".

    Returns:
        A list of job postings matching the search criteria.
    """
    # Phase 2: mock data only. Real source integration comes in Phase 4.
    return [
        {
            "id": "mock-001",
            "title": f"{role}",
            "company": "MockCorp AI",
            "location": location,
            "experience_min": 1,
            "experience_max": 3,
            "active_status": "active",
            "source": "mock",
        },
        {
            "id": "mock-002",
            "title": f"Senior {role}",
            "company": "MockCorp AI",
            "location": location,
            "experience_min": 5,
            "experience_max": 8,
            "active_status": "active",
            "source": "mock",
        },
    ]


if __name__ == "__main__":
    mcp.run()