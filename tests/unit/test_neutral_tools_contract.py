from __future__ import annotations


def test_neutral_tool_protocol_is_public_and_agent_tools_remain_compatible():
    from agent.tools import BaseTool as AgentBaseTool
    from agent.tools import ToolRegistry as AgentToolRegistry
    from tools import BaseTool, ToolError, ToolRegistry

    assert BaseTool is AgentBaseTool
    assert ToolRegistry is AgentToolRegistry
    assert issubclass(ToolError, Exception)
