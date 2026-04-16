"""
Toolregistry — 工具注册中心

管理所有 RAG 搜索工具的注册、查找和执行分发。
与 my-skill-try/registry.py 保持一致：async execute。
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class Toolregistry:
    """工具注册中心"""

    def __init__(self):
        self._tools: dict = {}

    def register(self, tool):
        """注册一个 tool"""
        self._tools[tool.name] = tool

    def get(self, name: str):
        """按名称获取 tool，不存在返回 None"""
        return self._tools.get(name)

    def list_all(self) -> list[dict]:
        """返回所有 tool 的 name + description，供前端展示"""
        return [
            {"name": t.name, "description": t.description}
            for t in self._tools.values()
        ]

    @property
    def tool_names(self) -> set[str]:
        """返回所有已注册工具名称集合"""
        return set(self._tools.keys())

    @property
    def get_definitions(self) -> list[dict]:
        """所有 tool 的 OpenAI function calling schema 列表"""
        return [t.schema for t in self._tools.values()]

    async def execute(self, name: str, **params):
        """按名称分发执行（async）"""
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"未知工具: {name}")
        return await tool.execute(**params)

    def __repr__(self):
        return f"Toolregistry(tools={list(self._tools.keys())})"
