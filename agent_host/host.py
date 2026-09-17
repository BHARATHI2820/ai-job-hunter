"""
AI Job Hunter — Host

Gemini model is selected dynamically through .env.

Example:

LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-3.8-flash
"""

import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

from google import genai
from mcp import Client as MCPClient

from core.logging_config import configure_logging, get_logger
from agent_host.graph import build_graph
from mcp_server.server import mcp


configure_logging()
logger = get_logger(__name__)


LLM_PROVIDER = os.getenv(
    "LLM_PROVIDER",
    "gemini",
).lower()

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash",
)


SEARCH_JOBS_FUNCTION = {
    "type": "function",
    "name": "search_jobs",
    "description": (
        "Search for jobs matching a role and location."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "role": {
                "type": "string",
                "description": (
                    "Job title or role, "
                    "e.g. 'GenAI Engineer'."
                ),
            },
            "location": {
                "type": "string",
                "description": (
                    "City or 'Remote', "
                    "e.g. 'Chennai'."
                ),
            },
        },
        "required": [
            "role",
            "location",
        ],
    },
}


VERIFY_JOB_ACTIVE_FUNCTION = {
    "type": "function",
    "name": "verify_job_active",
    "description": (
        "Check whether a specific job posting's "
        "application page is currently reachable."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "job_url": {
                "type": "string",
                "description": (
                    "The direct URL to the job posting."
                ),
            },
        },
        "required": [
            "job_url"
        ],
    },
}


TOOLS = [
    SEARCH_JOBS_FUNCTION,
    VERIFY_JOB_ACTIVE_FUNCTION,
]


async def run_query(
    user_input: str,
    previous_interaction_id: str | None = None,
) -> dict:
    """
    Run one AI Job Hunter query.

    previous_interaction_id is retained for API compatibility
    with the existing Streamlit UI. The generate_content-based
    implementation currently manages conversation state within
    the graph execution.
    """

    if LLM_PROVIDER != "gemini":
        raise ValueError(
            f"Unsupported LLM_PROVIDER: {LLM_PROVIDER!r}. "
            "Currently supported: gemini"
        )

    logger.info(
        f"[HOST] Starting query with model={GEMINI_MODEL}"
    )

    client = genai.Client()

    async with MCPClient(mcp) as mcp_client:
        app = build_graph(
            client,
            mcp_client,
            GEMINI_MODEL,
            TOOLS,
        )

        result = await app.ainvoke(
            {
                "user_input": user_input,
                "carry_over_interaction_id": (
                    previous_interaction_id
                ),
                "iteration": 0,
                "conversation": [],
            },
            config={
                "recursion_limit": 15
            },
        )

        logger.info(
            "[HOST] Final response generated"
        )

        return result


if __name__ == "__main__":
    result = asyncio.run(
        run_query(
            "Find GenAI Engineer jobs in Chennai, "
            "and verify if the top result is still active."
        )
    )

    logger.info(
        "[HOST] CLI query completed"
    )