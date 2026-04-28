from __future__ import annotations

import asyncio


def test_tool_registry_registers_lists_definitions_and_executes():
    from nutrimaster.agent.tools import BaseTool, ToolRegistry

    class EchoTool(BaseTool):
        name = "echo"
        description = "Echo input"

        @property
        def schema(self):
            return {
                "type": "function",
                "function": {
                    "name": self.name,
                    "description": self.description,
                    "parameters": {
                        "type": "object",
                        "properties": {"text": {"type": "string"}},
                    },
                },
            }

        async def execute(self, **kwargs):
            return kwargs["text"]

    registry = ToolRegistry()
    registry.register(EchoTool())

    assert registry.tool_names == {"echo"}
    assert registry.list_all() == [{"name": "echo", "description": "Echo input"}]
    assert registry.get_definitions[0]["function"]["name"] == "echo"
    assert asyncio.run(registry.execute("echo", text="hello")) == "hello"


def test_tool_registry_rejects_invalid_tools_and_unknown_execution():
    from nutrimaster.agent.tools import ToolRegistry

    registry = ToolRegistry()

    try:
        registry.register(object())
    except TypeError as exc:
        assert "BaseTool" in str(exc)
    else:
        raise AssertionError("Expected TypeError")

    try:
        asyncio.run(registry.execute("missing"))
    except ValueError as exc:
        assert "Unknown tool" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
