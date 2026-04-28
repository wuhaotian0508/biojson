from __future__ import annotations

from typing import Any


class AgentRuntime:
    """Stable NutriMaster boundary around the tool-calling agent."""

    def __init__(self, agent: Any):
        self._agent = agent

    @property
    def agent(self) -> Any:
        return self._agent

    async def run(
        self,
        *,
        user_input: str,
        user_id: str | None,
        model_id: str,
        history: list[dict],
        use_personal: bool,
        use_depth: bool,
        skill_prefs: dict,
        tool_overrides: dict,
    ):
        async for event in self._agent.run(
            user_input=user_input,
            user_id=user_id,
            model_id=model_id,
            history=history,
            use_personal=use_personal,
            use_depth=use_depth,
            skill_prefs=skill_prefs,
            tool_overrides=tool_overrides,
        ):
            yield event
