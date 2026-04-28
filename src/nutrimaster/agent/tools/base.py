from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar


class ToolError(Exception):
    """Raised by tools for expected tool execution failures."""


class BaseTool(ABC):
    name: ClassVar[str]
    description: ClassVar[str]

    @property
    @abstractmethod
    def schema(self) -> dict:
        """OpenAI-compatible function calling schema."""

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """Execute the tool and return text content."""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
