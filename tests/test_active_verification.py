"""
Phase 6 test — verifies the active-check heuristic against known,
stable HTTP status endpoints. Uses httpbin.org, a standard public
test service (no scraping, no auth, explicitly built for this purpose).
"""
from dotenv import load_dotenv
load_dotenv()
import pytest
from mcp import Client
from mcp_server.server import mcp
from core.verification.active_check import verify_url_active


@pytest.mark.anyio
async def test_verify_job_active_via_mcp_tool_call():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "verify_job_active", {"job_url": "https://httpbin.org/status/200"}
        )
        # Confirms structured_content is now populated correctly
        # after adding the TypedDict return annotation
        assert result.structured_content is not None
        payload = result.structured_content
        if "result" in payload:
            payload = payload["result"]
        assert payload["active_status"] == "active"

def test_verify_active_on_reachable_url():
    result = verify_url_active("https://httpbin.org/status/200")
    assert result["active_status"] == "active"


def test_verify_inactive_on_404():
    result = verify_url_active("https://httpbin.org/status/404")
    assert result["active_status"] == "inactive"


def test_verify_unknown_on_missing_url():
    result = verify_url_active(None)
    assert result["active_status"] == "unknown"
    assert "No job URL" in result["active_status_reason"]


def test_verify_unknown_on_unreachable_domain():
    result = verify_url_active("https://this-domain-does-not-exist-12345.invalid")
    assert result["active_status"] == "unknown"