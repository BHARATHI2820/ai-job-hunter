"""
AI Job Hunter — Host (Phase 6)

Now supports multi-step tool calling: Gemini may call search_jobs,
then decide to call verify_job_active, before producing a final answer.
"""

import asyncio
import json
import os
from pprint import pprint

from dotenv import load_dotenv

load_dotenv()

from google import genai
from mcp import Client as MCPClient

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


def _unwrap_mcp_result(mcp_result) -> dict | list:
    """
    MCP v2 populates structured_content when the tool's return type has
    a schema-able shape (e.g. list[dict]). For untyped/bare dict returns,
    structured_content may be None, and the real payload is only in
    content[0].text as a JSON string. Handle both cases.
    """
    if mcp_result.structured_content is not None:
        sc = mcp_result.structured_content
        if isinstance(sc, dict) and "result" in sc:
            return sc["result"]
        return sc

    # Fallback: extract from the text content block
    if mcp_result.content:
        for block in mcp_result.content:
            if getattr(block, "type", None) == "text":
                try:
                    return json.loads(block.text)
                except json.JSONDecodeError:
                    return block.text

    return None


async def run_query(user_input: str) -> None:
    client = genai.Client()

    async with MCPClient(mcp) as mcp_client:
        interaction = client.interactions.create(
            model=GEMINI_MODEL, input=user_input, tools=TOOLS
        )

        while True:
            fc_step = next((s for s in interaction.steps if s.type == "function_call"), None)

            if fc_step is None:
                print(f"\n[Gemini's final answer]\n{interaction.output_text}")
                return

            print(f"[Gemini decided to call] {fc_step.name}({fc_step.arguments})")

            mcp_result = await mcp_client.call_tool(fc_step.name, fc_step.arguments)
            tool_result = _unwrap_mcp_result(mcp_result)

            print("[MCP Server returned]")
            if isinstance(tool_result, list):
                for i, job in enumerate(tool_result, 1):
                    print(f"\n--- Job {i} ---")
                    for key, value in job.items():
                        print(f"{key}: {value}")
            else:
                pprint(tool_result, sort_dicts=False)

            interaction = client.interactions.create(
                model=GEMINI_MODEL,
                previous_interaction_id=interaction.id,
                tools=TOOLS,
                input=[
                    {
                        "type": "function_result",
                        "name": fc_step.name,
                        "call_id": fc_step.id,
                        "result": [{"type": "text", "text": json.dumps(tool_result)}],
                    }
                ],
            )


if __name__ == "__main__":
    asyncio.run(run_query("Find GenAI Engineer jobs in Chennai, and verify if the top result is still active."))