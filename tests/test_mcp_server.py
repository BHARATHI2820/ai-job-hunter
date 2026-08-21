"""
Phase 4 update — the in-memory tool-discovery test now needs Adzuna
credentials to run for real, since search_jobs() calls a live API.
We keep it as an integration test (skipped without credentials) rather
than removing it, so CI/dev without a key doesn't break.
"""

import os
from dotenv import load_dotenv
load_dotenv() 
import pytest

from mcp import Client


from mcp_server.server import mcp

requires_adzuna = pytest.mark.skipif(
    not (os.getenv("ADZUNA_APP_ID") and os.getenv("ADZUNA_APP_KEY")),
    reason="ADZUNA_APP_ID/ADZUNA_APP_KEY not set in .env",
)


@requires_adzuna
@pytest.mark.anyio
async def test_search_jobs_returns_real_results():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_jobs", {"role": "GenAI Engineer", "location": "Chennai"}
        )
        jobs = result.structured_content["result"]
        assert isinstance(jobs, list)
        if jobs:
            assert "title" in jobs[0]
            assert "source" in jobs[0]
            assert jobs[0]["source"] == "adzuna"