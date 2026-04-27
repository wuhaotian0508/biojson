from __future__ import annotations

from typing import Any


class AgentRuntime:
    """Stable NutriMaster boundary around the legacy RAG Agent."""

    def __init__(self, legacy_agent: Any):
        self._legacy_agent = legacy_agent

    @property
    def legacy_agent(self) -> Any:
        return self._legacy_agent

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
        async for event in self._legacy_agent.run(
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
