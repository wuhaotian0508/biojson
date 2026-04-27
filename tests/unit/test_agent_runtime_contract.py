from __future__ import annotations


def test_agent_runtime_delegates_to_legacy_agent_run():
    from agent.runtime import AgentRuntime

    class FakeLegacyAgent:
        def __init__(self):
            self.calls = []

        async def run(self, **kwargs):
            self.calls.append(kwargs)
            yield {"type": "text", "data": "ok"}

    legacy = FakeLegacyAgent()
    runtime = AgentRuntime(legacy)

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

    assert runtime.legacy_agent is legacy
    assert asyncio.run(collect()) == [{"type": "text", "data": "ok"}]
    assert legacy.calls == [
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
