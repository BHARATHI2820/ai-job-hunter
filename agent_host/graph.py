"""
LangGraph agent workflow — Phase 13 update.

Adds: carry_over_interaction_id (continues a PRIOR turn's conversation,
not just the current turn's tool loop), and last_search_results /
last_verification (structured data surfaced for UI rendering, separate
from whatever text Gemini chooses to narrate).
"""

import json
from typing import Any, TypedDict

from google.genai._gaos.lib.compat_errors import RateLimitError
from langgraph.graph import END, StateGraph
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential


class AgentState(TypedDict, total=False):
    user_input: str
    carry_over_interaction_id: str | None
    interaction: Any
    pending_call_name: str | None
    pending_call_args: dict | None
    pending_call_id: str | None
    tool_result: Any
    final_answer: str | None
    iteration: int
    last_search_results: list[dict] | None
    last_verification: dict | None


def _unwrap_mcp_result(mcp_result) -> dict | list:
    if mcp_result.structured_content is not None:
        sc = mcp_result.structured_content
        if isinstance(sc, dict) and "result" in sc:
            return sc["result"]
        return sc
    if mcp_result.content:
        for block in mcp_result.content:
            if getattr(block, "type", None) == "text":
                try:
                    return json.loads(block.text)
                except json.JSONDecodeError:
                    return block.text
    return None


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, RateLimitError):
        return True
    message = str(exc).lower()
    return any(m in message for m in ("internal server error", "service unavailable", "503", "500"))


@retry(
    retry=retry_if_exception(_is_retryable),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    stop=stop_after_attempt(4),
    reraise=True,
)
def _create_interaction_with_retry(genai_client, **kwargs):
    return genai_client.interactions.create(**kwargs)


def build_graph(genai_client, mcp_client, gemini_model: str, tools: list[dict]):

    def call_llm_node(state: AgentState) -> dict:
        if state.get("tool_result") is not None and state.get("pending_call_name"):
            interaction = _create_interaction_with_retry(
                genai_client,
                model=gemini_model,
                previous_interaction_id=state["interaction"].id,
                tools=tools,
                input=[
                    {
                        "type": "function_result",
                        "name": state["pending_call_name"],
                        "call_id": state["pending_call_id"],
                        "result": [{"type": "text", "text": json.dumps(state["tool_result"])}],
                    }
                ],
            )
        else:
            kwargs = {"model": gemini_model, "input": state["user_input"], "tools": tools}
            carry_over = state.get("carry_over_interaction_id")
            if carry_over:
                kwargs["previous_interaction_id"] = carry_over
            interaction = _create_interaction_with_retry(genai_client, **kwargs)

        fc_step = next((s for s in interaction.steps if s.type == "function_call"), None)
        updates: dict = {
            "interaction": interaction,
            "iteration": state.get("iteration", 0) + 1,
            "tool_result": None,
        }
        if fc_step:
            print(f"[Gemini decided to call] {fc_step.name}({fc_step.arguments})")
            updates.update(
                {
                    "pending_call_name": fc_step.name,
                    "pending_call_args": fc_step.arguments,
                    "pending_call_id": fc_step.id,
                }
            )
        else:
            updates.update({"final_answer": interaction.output_text, "pending_call_name": None})
        return updates

    async def execute_tool_node(state: AgentState) -> dict:
        name = state["pending_call_name"]
        mcp_result = await mcp_client.call_tool(name, state["pending_call_args"])
        result = _unwrap_mcp_result(mcp_result)
        summary = f"{len(result)} job(s)" if isinstance(result, list) else result
        print(f"[MCP Server returned] {summary}")

        updates: dict = {"tool_result": result}
        if name == "search_jobs" and isinstance(result, list):
            updates["last_search_results"] = result
        elif name == "verify_job_active" and isinstance(result, dict):
            updates["last_verification"] = result
        return updates

    def no_jobs_shortcut_node(state: AgentState) -> dict:
        print("[GRAPH] search_jobs returned 0 results — skipping extra Gemini call")
        return {
            "final_answer": (
                "No jobs matched your search after filtering. Try a different "
                "role, a broader location, or Remote."
            ),
            "last_search_results": [],
        }

    def route_after_llm(state: AgentState) -> str:
        return "end" if state.get("final_answer") else "execute_tool"

    def route_after_tool(state: AgentState) -> str:
        if (
            state.get("pending_call_name") == "search_jobs"
            and isinstance(state.get("tool_result"), list)
            and len(state["tool_result"]) == 0
        ):
            return "no_jobs"
        return "call_llm"

    graph = StateGraph(AgentState)
    graph.add_node("call_llm", call_llm_node)
    graph.add_node("execute_tool", execute_tool_node)
    graph.add_node("no_jobs", no_jobs_shortcut_node)
    graph.set_entry_point("call_llm")
    graph.add_conditional_edges(
        "call_llm", route_after_llm, {"execute_tool": "execute_tool", "end": END}
    )
    graph.add_conditional_edges(
        "execute_tool", route_after_tool, {"no_jobs": "no_jobs", "call_llm": "call_llm"}
    )
    graph.add_edge("no_jobs", END)

    return graph.compile()