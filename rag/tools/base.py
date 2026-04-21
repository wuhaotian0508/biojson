"""
BaseTool — 所有工具的抽象基类

参照 EvoMaster 的 BaseTool 模式，强制 name/description/schema/execute 接口。
保留项目已有的 async execute(**kwargs) 签名。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar


class ToolError(Exception):
    """工具执行错误（区别于普通 Exception，便于 agent 捕获分类）"""


class BaseTool(ABC):
    """所有 RAG 工具的抽象基类。

    子类必须:
      1. 定义 name: ClassVar[str] 和 description: ClassVar[str]
      2. 实现 schema property（OpenAI function calling 格式）
      3. 实现 async execute(**kwargs) -> str
    """
    name: ClassVar[str]
    description: ClassVar[str]

    @property
    @abstractmethod
    def schema(self) -> dict:
        """返回 OpenAI function calling schema dict。"""
        ...

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """执行工具，返回结果文本。"""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
