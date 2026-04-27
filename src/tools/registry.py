from __future__ import annotations

import logging

from tools.base import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if not isinstance(tool, BaseTool):
            raise TypeError(
                f"Tool {tool!r} must inherit BaseTool; got {type(tool).__name__}"
            )
        if tool.name in self._tools:
            logger.warning("Tool %r registered more than once; replacing previous instance", tool.name)
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_all(self) -> list[dict]:
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self._tools.values()
        ]

    @property
    def tool_names(self) -> set[str]:
        return set(self._tools)

    @property
    def get_definitions(self) -> list[dict]:
        return [tool.schema for tool in self._tools.values()]

    async def execute(self, name: str, **params):
        tool = self._tools.get(name)
        if tool is None:
            raise ValueError(f"Unknown tool: {name}")
        return await tool.execute(**params)

    def __repr__(self) -> str:
        return f"ToolRegistry(tools={list(self._tools)})"
