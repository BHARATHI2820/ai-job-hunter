"""
Phase 13 test — confirms call_llm_node includes previous_interaction_id
on the FIRST call of a new graph invocation when carry_over is provided,
which is the actual mechanism that makes multi-turn chat context work.
Uses a fake genai client to capture the kwargs it was called with,
without making a real API call.
"""

import pytest

from agent_host.graph import build_graph


class _FakeInteraction:
    def __init__(self, id_):
        self.id = id_
        self.steps = []
        self.output_text = "fake answer"


class _FakeInteractionsAPI:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeInteraction("fake-interaction-id")


class _FakeGenAIClient:
    def __init__(self):
        self.interactions = _FakeInteractionsAPI()


class _FakeMCPClient:
    async def call_tool(self, name, args):
        raise AssertionError("should not be called in this test")


@pytest.mark.anyio
async def test_carry_over_interaction_id_passed_on_first_call():
    fake_client = _FakeGenAIClient()
    app = build_graph(fake_client, _FakeMCPClient(), "fake-model", [])

    await app.ainvoke(
        {
            "user_input": "only show active ones",
            "carry_over_interaction_id": "prior-turn-id-123",
            "iteration": 0,
        }
    )

    assert len(fake_client.interactions.calls) == 1
    assert fake_client.interactions.calls[0].get("previous_interaction_id") == "prior-turn-id-123"


@pytest.mark.anyio
async def test_no_carry_over_means_fresh_conversation():
    fake_client = _FakeGenAIClient()
    app = build_graph(fake_client, _FakeMCPClient(), "fake-model", [])

    await app.ainvoke({"user_input": "Find jobs", "iteration": 0})

    assert "previous_interaction_id" not in fake_client.interactions.calls[0]