"""
AI Job Hunter — Host (Phase 3)

Bridges Gemini's tool-calling with the MCP Client + Server.
Scope: Gemini + MCP Client + MCP Server + search_jobs() only.
No real job source, DB, RAG, or filtering yet.
"""

import asyncio
import json
import os

from dotenv import load_dotenv
from google import genai
from mcp import Client as MCPClient

from mcp_server.server import mcp

load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")

# Manually declared to match the MCP server's search_jobs() signature.
# (Auto-generating this from mcp_client.list_tools() is a natural
# improvement for a later phase — kept manual now for clarity.)
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


async def run_query(user_input: str) -> None:
    client = genai.Client()

    async with MCPClient(mcp) as mcp_client:
        interaction = client.interactions.create(
            model=GEMINI_MODEL,
            input=user_input,
            tools=[SEARCH_JOBS_FUNCTION],
        )

        fc_step = next((s for s in interaction.steps if s.type == "function_call"), None)

        if fc_step is None:
            print(interaction.output_text)
            return

        print(f"[Gemini decided to call] {fc_step.name}({fc_step.arguments})")

        # MCP Client executes the tool call — Gemini never touches this step.
        mcp_result = await mcp_client.call_tool(fc_step.name, fc_step.arguments)
        tool_result = mcp_result.structured_content

        print(f"[MCP Server returned] {tool_result}")

        final_interaction = client.interactions.create(
            model=GEMINI_MODEL,
            previous_interaction_id=interaction.id,
            tools=[SEARCH_JOBS_FUNCTION],
            input=[
                {
                    "type": "function_result",
                    "name": fc_step.name,
                    "call_id": fc_step.id,
                    "result": [{"type": "text", "text": json.dumps(tool_result)}],
                }
            ],
        )

        print(f"\n[Gemini's final answer]\n{final_interaction.output_text}")


if __name__ == "__main__":
    asyncio.run(run_query("Find GenAI Engineer jobs in Chennai"))