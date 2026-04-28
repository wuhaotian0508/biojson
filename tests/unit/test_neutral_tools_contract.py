from __future__ import annotations


def test_neutral_tool_protocol_is_public_and_agent_tools_remain_compatible():
    from nutrimaster.agent.tools import BaseTool as AgentBaseTool
    from nutrimaster.agent.tools import ToolRegistry as AgentToolRegistry
    from nutrimaster.agent.tools import BaseTool, ToolError, ToolRegistry

    assert BaseTool is AgentBaseTool
    assert ToolRegistry is AgentToolRegistry
    assert issubclass(ToolError, Exception)
