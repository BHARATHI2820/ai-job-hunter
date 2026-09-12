"""
AI Job Hunter — Host (Phase 13)

run_query() now returns the full result dict so callers (CLI here,
Streamlit in ui/streamlit_app.py) can access final_answer, the
interaction ID for context continuation, and structured job results.
"""

import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

from google import genai
from mcp import Client as MCPClient

from agent_host.graph import build_graph
from mcp_server.server import mcp

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")

SEARCH_JOBS_FUNCTION = {
    "type": "function",
    "name": "search_jobs",
    "description": "Search for jobs matching a role and location.",
    "parameters": {
        "type": "object",
        "properties": {
            "role": {"type": "string", "description": "Job title or role, e.g. 'GenAI Engineer'."},
            "location": {"type": "string", "description": "City or 'Remote', e.g. 'Chennai'."},
        },
        "required": ["role", "location"],
    },
}

VERIFY_JOB_ACTIVE_FUNCTION = {
    "type": "function",
    "name": "verify_job_active",
    "description": "Check whether a specific job posting's application page is currently reachable.",
    "parameters": {
        "type": "object",
        "properties": {
            "job_url": {"type": "string", "description": "The direct URL to the job posting."},
        },
        "required": ["job_url"],
    },
}

TOOLS = [SEARCH_JOBS_FUNCTION, VERIFY_JOB_ACTIVE_FUNCTION]


async def run_query(user_input: str, previous_interaction_id: str | None = None) -> dict:
    client = genai.Client()

    async with MCPClient(mcp) as mcp_client:
        app = build_graph(client, mcp_client, GEMINI_MODEL, TOOLS)

        result = await app.ainvoke(
            {
                "user_input": user_input,
                "carry_over_interaction_id": previous_interaction_id,
                "iteration": 0,
            },
            config={"recursion_limit": 15},
        )
        return result


if __name__ == "__main__":
    result = asyncio.run(
        run_query("Find GenAI Engineer jobs in Chennai, and verify if the top result is still active.")
    )
    print(f"\n[Gemini's final answer]\n{result.get('final_answer')}")