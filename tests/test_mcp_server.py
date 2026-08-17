"""
Phase 2 test — verifies the MCP server exposes and correctly executes
search_jobs() via an in-memory client (no subprocess, no network).
"""

import pytest
from mcp import Client
from mcp_server.server import mcp


@pytest.mark.anyio
async def test_search_jobs_returns_mock_results():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_jobs", {"role": "GenAI Engineer", "location": "Chennai"}
        )
        jobs = result.structured_content["result"]

        assert len(jobs) == 2
        assert jobs[0]["title"] == "GenAI Engineer"
        assert jobs[0]["location"] == "Chennai"
        assert jobs[1]["title"] == "Senior GenAI Engineer"