import json
import re
from typing import Any, TypedDict

from google import genai
from google.genai import types
from langgraph.graph import END, StateGraph

from core.logging_config import get_logger

logger = get_logger(__name__)


class AgentState(TypedDict, total=False):
    user_input: str
    carry_over_interaction_id: str | None

    interaction: Any
    conversation: list[Any]

    pending_call_name: str | None
    pending_call_args: dict | None
    pending_call_id: str | None

    tool_result: Any

    final_answer: str | None

    iteration: int

    last_search_results: list[dict] | None
    last_verification: dict | None

    fallback_mode: bool


def _unwrap_mcp_result(mcp_result) -> dict | list:
    if mcp_result.structured_content is not None:
        structured = mcp_result.structured_content

        if isinstance(structured, dict) and "result" in structured:
            return structured["result"]

        return structured

    if mcp_result.content:
        for block in mcp_result.content:
            if getattr(block, "type", None) == "text":
                try:
                    return json.loads(block.text)
                except json.JSONDecodeError:
                    return block.text

    return None


def _build_gemini_tools(tools: list[dict]) -> list[types.Tool]:
    declarations = []

    for tool in tools:
        declarations.append(
            types.FunctionDeclaration(
                name=tool["name"],
                description=tool.get("description", ""),
                parameters_json_schema=tool.get(
                    "parameters",
                    {
                        "type": "object",
                        "properties": {},
                    },
                ),
            )
        )

    return [
        types.Tool(
            function_declarations=declarations
        )
    ]


def _text_content(text: str) -> types.Content:
    return types.Content(
        role="user",
        parts=[
            types.Part(text=text)
        ],
    )


def _function_response_content(
    name: str,
    result: Any,
    call_id: str | None = None,
) -> types.Content:
    response_kwargs = {
        "name": name,
        "response": {
            "result": result,
        },
    }

    if call_id:
        response_kwargs["id"] = call_id

    return types.Content(
        role="user",
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    **response_kwargs
                )
            )
        ],
    )


def _generate_content(
    client: genai.Client,
    model: str,
    conversation: list,
    tools: list[types.Tool],
):
    return client.models.generate_content(
        model=model,
        contents=conversation,
        config=types.GenerateContentConfig(
            tools=tools,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        ),
    )


def _extract_fallback_search_args(user_input: str) -> dict:
    """
    Deterministically extract role and location from common
    natural-language job search queries when Gemini is unavailable.
    """

    import re

    text = " ".join(user_input.strip().split())

    # Normalize common query prefixes.
    text = re.sub(
        r"^(find|show me|show|search for|search|looking for|i want|give me|"
        r"get me|fetch|list|list me)\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # Extract location from phrases such as:
    # "in Chennai"
    # "at Chennai"
    # "near Chennai"
    location_match = re.search(
        r"\b(?:in|at|near)\s+(.+?)\s*$",
        text,
        flags=re.IGNORECASE,
    )

    if location_match:
        location = location_match.group(1).strip()

        # Remove trailing punctuation.
        location = location.rstrip(" .,!?")

        role_part = text[:location_match.start()].strip()
    else:
        location = "Remote"
        role_part = text

    # Remove common "jobs" wording from the role.
    role_part = re.sub(
        r"\b(?:jobs?|job\s+openings?|openings?|vacancies?)\b",
        "",
        role_part,
        flags=re.IGNORECASE,
    )

    # Clean leftover punctuation / whitespace.
    role = re.sub(r"\s+", " ", role_part).strip(" ,.-")

    # Safety fallback.
    if not role:
        role = text.strip()

    return {
        "role": role,
        "location": location,
    }


def _fallback_final_answer(
    state: AgentState,
    result: Any,
) -> str:
    if isinstance(result, list):
        count = len(result)

        if count == 0:
            return (
                "No jobs matched your search after filtering. "
                "Try a different role, a broader location, or Remote."
            )

        return (
            f"I found {count} matching job(s). "
            "I've ranked them using the configured matching, "
            "experience, and freshness signals."
        )

    if isinstance(result, dict):
        if result.get("active") is True:
            return "The job posting is currently reachable."
        if result.get("active") is False:
            return "The job posting does not appear to be active."

    return "The requested operation was completed."


def build_graph(
    genai_client: genai.Client,
    mcp_client,
    gemini_model: str,
    tools: list[dict],
):
    gemini_tools = _build_gemini_tools(tools)

    def call_llm_node(state: AgentState) -> dict:
        iteration = state.get("iteration", 0)

        if iteration >= 10:
            return {
                "final_answer": (
                    "I couldn't complete the search within the "
                    "allowed processing steps."
                ),
                "pending_call_name": None,
            }

        conversation = list(
            state.get("conversation") or []
        )

        if not conversation:
            conversation.append(
                _text_content(state["user_input"])
            )

        # ---------------------------------------------------------
        # FALLBACK MODE
        # ---------------------------------------------------------
        if state.get("fallback_mode"):
            args = _extract_fallback_search_args(
                state["user_input"]
            )

            logger.info(
                "[LLM] Using deterministic fallback parser"
            )

            return {
                "iteration": iteration + 1,
                "pending_call_name": "search_jobs",
                "pending_call_args": args,
                "pending_call_id": None,
                "conversation": conversation,
                "tool_result": None,
            }

        # ---------------------------------------------------------
        # GEMINI
        # ---------------------------------------------------------
        logger.info(
            f"[LLM] Calling {gemini_model} "
            f"(iteration={iteration + 1})"
        )

        try:
            response = _generate_content(
                genai_client,
                gemini_model,
                conversation,
                gemini_tools,
            )

        except Exception as exc:
            message = str(exc).lower()

            llm_unavailable = any(
                marker in message
                for marker in (
                    "503",
                    "unavailable",
                    "high demand",
                    "internal server error",
                    "500",
                    "429",
                    "resource_exhausted",
                )
            )

            if llm_unavailable:
                logger.warning(
                    "[LLM] Gemini unavailable or quota exhausted — "
                    "using fallback handling"
                )

                # -------------------------------------------------
                # We already have search results.
                # Do NOT execute search_jobs again.
                # -------------------------------------------------
                existing_results = state.get(
                    "last_search_results"
                )

                if isinstance(existing_results, list):
                    return {
                        "iteration": iteration + 1,
                        "final_answer": _fallback_final_answer(
                            state,
                            existing_results,
                        ),
                        "last_search_results": existing_results,
                        "pending_call_name": None,
                        "pending_call_args": None,
                        "pending_call_id": None,
                        "conversation": conversation,
                        "tool_result": existing_results,
                        "fallback_mode": True,
                    }

                # -------------------------------------------------
                # Gemini failed before any tool execution.
                # Use deterministic search fallback.
                # -------------------------------------------------
                args = _extract_fallback_search_args(
                    state["user_input"]
                )

                return {
                    "iteration": iteration + 1,
                    "pending_call_name": "search_jobs",
                    "pending_call_args": args,
                    "pending_call_id": None,
                    "conversation": conversation,
                    "tool_result": None,
                    "fallback_mode": True,
                }

            raise

        function_calls = list(
            response.function_calls or []
        )

        updates = {
            "iteration": iteration + 1,
            "interaction": response,
            "conversation": conversation,
            "tool_result": None,
        }

        if function_calls:
            call = function_calls[0]

            logger.info(
                f"[AGENT] Tool selected: {call.name}"
            )

            if response.candidates:
                model_content = (
                    response.candidates[0].content
                )

                if model_content is not None:
                    conversation.append(
                        model_content
                    )

            updates.update(
                {
                    "pending_call_name": call.name,
                    "pending_call_args": dict(
                        call.args or {}
                    ),
                    "pending_call_id": getattr(
                        call,
                        "id",
                        None,
                    ),
                }
            )

            return updates

        updates.update(
            {
                "final_answer": (
                    response.text
                    or "I couldn't generate a response."
                ),
                "pending_call_name": None,
                "pending_call_args": None,
                "pending_call_id": None,
            }
        )

        return updates

    async def execute_tool_node(
        state: AgentState,
    ) -> dict:
        name = state["pending_call_name"]
        args = state.get("pending_call_args") or {}

        logger.info(
            f"[MCP] Executing {name} with args={args}"
        )

        mcp_result = await mcp_client.call_tool(
            name,
            args,
        )

        result = _unwrap_mcp_result(
            mcp_result
        )

        if isinstance(result, list):
            logger.info(
                f"[MCP] {name} returned "
                f"{len(result)} job(s)"
            )
        else:
            logger.info(
                f"[MCP] {name} returned {result}"
            )

        updates = {
            "tool_result": result
        }

        if (
            name == "search_jobs"
            and isinstance(result, list)
        ):
            updates["last_search_results"] = result

        elif (
            name == "verify_job_active"
            and isinstance(result, dict)
        ):
            updates["last_verification"] = result

        conversation = list(
            state.get("conversation") or []
        )

        if not state.get("fallback_mode"):
            conversation.append(
                _function_response_content(
                    name=name,
                    result=result,
                    call_id=state.get(
                        "pending_call_id"
                    ),
                )
            )

        updates["conversation"] = conversation

        # ---------------------------------------------------------
        # FALLBACK FINAL RESPONSE
        # ---------------------------------------------------------
        if state.get("fallback_mode"):
            updates.update(
                {
                    "final_answer": _fallback_final_answer(
                        state,
                        result,
                    ),
                    "pending_call_name": None,
                    "pending_call_args": None,
                    "pending_call_id": None,
                }
            )

        return updates

    def no_jobs_shortcut_node(
        state: AgentState,
    ) -> dict:
        logger.info(
            "[GRAPH] search_jobs returned 0 results"
        )

        return {
            "final_answer": (
                "No jobs matched your search after filtering. "
                "Try a different role, a broader location, or Remote."
            ),
            "last_search_results": [],
            "pending_call_name": None,
        }

    def route_after_llm(
        state: AgentState,
    ) -> str:
        if state.get("final_answer"):
            return "end"

        return "execute_tool"

    def route_after_tool(
        state: AgentState,
    ) -> str:
        if (
            state.get("pending_call_name") == "search_jobs"
            and isinstance(
                state.get("tool_result"),
                list,
            )
            and len(state["tool_result"]) == 0
        ):
            return "no_jobs"

        if state.get("final_answer"):
            return "end"

        return "call_llm"

    graph = StateGraph(AgentState)

    graph.add_node(
        "call_llm",
        call_llm_node,
    )

    graph.add_node(
        "execute_tool",
        execute_tool_node,
    )

    graph.add_node(
        "no_jobs",
        no_jobs_shortcut_node,
    )

    graph.set_entry_point("call_llm")

    graph.add_conditional_edges(
        "call_llm",
        route_after_llm,
        {
            "execute_tool": "execute_tool",
            "end": END,
        },
    )

    graph.add_conditional_edges(
        "execute_tool",
        route_after_tool,
        {
            "no_jobs": "no_jobs",
            "call_llm": "call_llm",
            "end": END,
        },
    )

    graph.add_edge(
        "no_jobs",
        END,
    )

    return graph.compile()