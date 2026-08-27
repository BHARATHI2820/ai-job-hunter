"""
LangGraph agent workflow — Phase 12 (+ Phase 12b retry hardening).

Wraps the Gemini <-> MCP tool-calling loop (Phase 3-6) into an explicit
StateGraph. Adds one genuine conditional branch beyond the previous
manual loop: an empty search_jobs() result short-circuits straight to
a fixed response, skipping a second Gemini call entirely — the same
cost-reduction discipline as section 32's hard-filter-before-LLM logic,
applied here at the orchestration layer.

Retry/backoff note: the google-genai SDK already retries transient 5xx
errors internally (it depends on tenacity itself). What was actually
crashing this project was the 429 free-tier quota error surfacing as
a RateLimitError that the SDK does NOT retry on its own, since retrying
a quota-exceeded error blindly would be wrong behavior for a paid,
production caller. We add our own bounded retry specifically for that
case. This CANNOT and does not pretend to fix a genuinely exhausted
daily quota — after the retry budget is spent, the error still surfaces
to the caller, which is the correct, honest behavior.
"""

import json
from typing import Any, TypedDict

from google.genai._gaos.lib.compat_errors import RateLimitError
from langgraph.graph import END, StateGraph
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)


class AgentState(TypedDict, total=False):
    user_input: str
    interaction: Any
    pending_call_name: str | None
    pending_call_args: dict | None
    pending_call_id: str | None
    tool_result: Any
    final_answer: str | None
    iteration: int


def _unwrap_mcp_result(mcp_result) -> dict | list:
    """Same unwrap logic as Phase 6 — MCP v2 result shape handling."""
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
    """RateLimitError (429) is the confirmed, deliberately-not-auto-retried
    case that actually crashed this project. As a defensive fallback, also
    retry any other exception whose message clearly indicates a transient
    server-side failure (5xx) that happened to slip past the SDK's own
    internal retry — this is best-effort text matching, not a verified
    exception hierarchy, since we don't have a confirmed class name for
    every transient error the SDK might raise."""
    if isinstance(exc, RateLimitError):
        return True
    message = str(exc).lower()
    transient_markers = ("internal server error", "service unavailable", "503", "500")
    return any(marker in message for marker in transient_markers)


@retry(
    retry=retry_if_exception(_is_retryable),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    stop=stop_after_attempt(4),
    reraise=True,  # after exhausting retries, the real error surfaces — no silent failure
)
def _create_interaction_with_retry(genai_client, **kwargs):
    return genai_client.interactions.create(**kwargs)


def build_graph(genai_client, mcp_client, gemini_model: str, tools: list[dict]):
    """Builds the compiled LangGraph. Takes live client instances rather
    than constructing them internally, since they're managed by the
    caller's async context (MCP connection lifecycle in particular)."""

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
            interaction = _create_interaction_with_retry(
                genai_client, model=gemini_model, input=state["user_input"], tools=tools
            )

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
        mcp_result = await mcp_client.call_tool(
            state["pending_call_name"], state["pending_call_args"]
        )
        result = _unwrap_mcp_result(mcp_result)
        summary = f"{len(result)} job(s)" if isinstance(result, list) else result
        print(f"[MCP Server returned] {summary}")
        return {"tool_result": result}

    def no_jobs_shortcut_node(state: AgentState) -> dict:
        print("[GRAPH] search_jobs returned 0 results — skipping extra Gemini call")
        return {
            "final_answer": (
                "No jobs matched your search after filtering. Try a different "
                "role, a broader location, or Remote."
            )
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