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
        tool_names = {"rag_search"}
        get_definitions = [
            {
                "type": "function",
                "function": {"name": "rag_search", "description": "rag"},
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


def test_canonical_agent_numbers_multiple_rag_calls_with_one_global_registry():
    import asyncio
    import json

    from nutrimaster.agent.agent import Agent
    from nutrimaster.rag.evidence import EvidenceItem, EvidencePacket

    class FakeRegistry:
        tool_names = {"rag_search"}
        get_definitions = [
            {
                "type": "function",
                "function": {"name": "rag_search", "description": "rag"},
            }
        ]

        async def execute(self, tool_name, **args):
            if args["query"] == "first":
                return EvidencePacket(
                    query="first",
                    mode="normal",
                    items=[
                        EvidenceItem(
                            source_id="1",
                            source_type="gene_db",
                            title="First GS paper",
                            content="GS1 evidence",
                        )
                    ],
                )
            return EvidencePacket(
                query="second",
                mode="normal",
                items=[
                    EvidenceItem(
                        source_id="1",
                        source_type="pubmed",
                        title="Second GS paper",
                        content="GS2 evidence",
                    )
                ],
            )

    class FakeSkillLoader:
        def list_dir(self, user_id=None):
            return []

    calls = []

    async def call_llm(messages, tools=None, model_id="", **kwargs):
        calls.append(messages)
        if len(calls) == 1:
            return SimpleNamespace(
                content="",
                tool_calls=[_tool_call("call-1", "rag_search", {"query": "first"})],
            )
        if len(calls) == 2:
            assert "[1] First GS paper" in messages[-1]["content"]
            return SimpleNamespace(
                content="",
                tool_calls=[_tool_call("call-2", "rag_search", {"query": "second"})],
            )
        assert "[2] Second GS paper" in messages[-1]["content"]
        return SimpleNamespace(content="see [1] and [2]", tool_calls=None)

    def _tool_call(call_id, name, arguments):
        return SimpleNamespace(
            id=call_id,
            function=SimpleNamespace(name=name, arguments=json.dumps(arguments)),
        )

    agent = Agent(
        registry=FakeRegistry(),
        skill_loader=FakeSkillLoader(),
        call_llm=call_llm,
    )

    events = asyncio.run(_collect(agent.run(user_input="GS families")))
    tool_results = [event for event in events if event["type"] == "tool_result"]
    citations = next(event["data"] for event in events if event["type"] == "citations")

    assert "[1] First GS paper" in tool_results[0]["content"]
    assert "[2] Second GS paper" in tool_results[1]["content"]
    assert [citation["tool_index"] for citation in citations] == [1, 2]


async def _collect(async_iter):
    return [item async for item in async_iter]
