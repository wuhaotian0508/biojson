from __future__ import annotations


def test_agent_runtime_delegates_to_agent_run():
    from nutrimaster.agent.runtime import AgentRuntime

    class FakeAgent:
        def __init__(self):
            self.calls = []

        async def run(self, **kwargs):
            self.calls.append(kwargs)
            yield {"type": "text", "data": "ok"}

    agent = FakeAgent()
    runtime = AgentRuntime(agent)

    async def collect():
        return [
            event
            async for event in runtime.run(
                user_input="query",
                user_id="user-1",
                model_id="primary",
                history=[],
                use_personal=False,
                use_depth=True,
                skill_prefs={},
                tool_overrides={},
            )
        ]

    import asyncio

    assert runtime.agent is agent
    assert asyncio.run(collect()) == [{"type": "text", "data": "ok"}]
    assert agent.calls == [
        {
            "user_input": "query",
            "user_id": "user-1",
            "model_id": "primary",
            "history": [],
            "use_personal": False,
            "use_depth": True,
            "skill_prefs": {},
            "tool_overrides": {},
        }
    ]
