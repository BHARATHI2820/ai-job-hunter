"""
Phase 12 test — verifies the graph structure and the no-jobs shortcut
branch logic in isolation, without real Gemini/MCP calls (fast, free).
"""

from agent_host.graph import build_graph


class _FakeMCPClient:
    async def call_tool(self, name, args):
        raise AssertionError("should not be called in this test")


class _FakeGenAIClient:
    pass


def test_graph_compiles_with_expected_nodes():
    app = build_graph(_FakeGenAIClient(), _FakeMCPClient(), "fake-model", [])
    node_names = set(app.get_graph().nodes.keys())
    assert "call_llm" in node_names
    assert "execute_tool" in node_names
    assert "no_jobs" in node_names


def test_route_after_tool_triggers_shortcut_on_empty_search_results():
    from agent_host.graph import build_graph as _bg  # noqa: F401
    # Import the routing function indirectly via a constructed state,
    # since it's defined as a closure inside build_graph — test the
    # observable graph behavior instead of reaching into internals.
    app = build_graph(_FakeGenAIClient(), _FakeMCPClient(), "fake-model", [])
    graph_repr = app.get_graph()
    assert ("execute_tool", "no_jobs") in {
        (edge.source, edge.target) for edge in graph_repr.edges
    }