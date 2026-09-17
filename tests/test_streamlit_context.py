"""
Phase 17 test — confirms conversation handling for the
generate_content()-based Gemini agent.

The previous implementation used Gemini Interactions API and passed
previous_interaction_id directly to interactions.create().

The current implementation maintains conversation state inside the
LangGraph invocation, so these tests verify that:
- a fresh invocation starts with the user's input
- carry_over_interaction_id does not break a fresh graph invocation
- no real Gemini API call is made
"""

import pytest

from agent_host.graph import build_graph


class _FakeResponse:
    def __init__(self):
        self.function_calls = []
        self.text = "fake answer"
        self.candidates = []


class _FakeModelsAPI:
    def __init__(self):
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeResponse()


class _FakeGenAIClient:
    def __init__(self):
        self.models = _FakeModelsAPI()


class _FakeMCPClient:
    async def call_tool(self, name, args):
        raise AssertionError(
            "MCP tool should not be called in this test"
        )


@pytest.mark.anyio
async def test_carry_over_interaction_id_does_not_break_first_call():
    fake_client = _FakeGenAIClient()

    app = build_graph(
        fake_client,
        _FakeMCPClient(),
        "fake-model",
        [],
    )

    await app.ainvoke(
        {
            "user_input": "only show active ones",
            "carry_over_interaction_id": "prior-turn-id-123",
            "iteration": 0,
        }
    )

    assert len(fake_client.models.calls) == 1

    call = fake_client.models.calls[0]

    assert call["model"] == "fake-model"

    contents = call["contents"]

    assert len(contents) == 1
    assert contents[0].parts[0].text == "only show active ones"


@pytest.mark.anyio
async def test_no_carry_over_means_fresh_conversation():
    fake_client = _FakeGenAIClient()

    app = build_graph(
        fake_client,
        _FakeMCPClient(),
        "fake-model",
        [],
    )

    await app.ainvoke(
        {
            "user_input": "Find jobs",
            "iteration": 0,
        }
    )

    assert len(fake_client.models.calls) == 1

    call = fake_client.models.calls[0]

    contents = call["contents"]

    assert len(contents) == 1
    assert contents[0].parts[0].text == "Find jobs"