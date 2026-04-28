from __future__ import annotations

import inspect
from types import SimpleNamespace


def test_canonical_agent_does_not_delegate_to_legacy_core_agent():
    import nutrimaster.agent.agent as agent_module

    source = inspect.getsource(agent_module)

    assert "core.agent" not in source
    assert "importlib" not in source


def test_canonical_agent_streams_direct_llm_answer_without_tool_call():
    import asyncio

    from nutrimaster.agent.agent import Agent

    class FakeRegistry:
        tool_names = {"read_tool"}
        get_definitions = [
            {
                "type": "function",
                "function": {"name": "read_tool", "description": "read"},
            }
        ]

    class FakeSkillLoader:
        def list_dir(self, user_id=None):
            return []

    async def call_llm(messages, tools=None, model_id="", **kwargs):
        return SimpleNamespace(content="hello answer", tool_calls=None)

    async def call_llm_stream(*args, **kwargs):
        yield SimpleNamespace()

    agent = Agent(
        registry=FakeRegistry(),
        skill_loader=FakeSkillLoader(),
        call_llm=call_llm,
        call_llm_stream=call_llm_stream,
    )

    events = asyncio.run(
        _collect(
            agent.run(
                user_input="hello",
                history=[],
                use_personal=False,
                use_depth=False,
                skill_prefs={},
                tool_overrides={},
            )
        )
    )

    assert events[0]["type"] == "tools_enabled"
    assert {"type": "text", "data": "hello answer"} in events
    assert events[-1] == {"type": "done"}


async def _collect(async_iter):
    return [item async for item in async_iter]
