from __future__ import annotations


def test_default_user_tool_policy_preserves_filesystem_and_shell_tools():
    from nutrimaster.agent.tool_policy import ToolPolicy

    policy = ToolPolicy.default_user()

    assert {"execute_shell", "read_tool", "write_tool"}.issubset(policy.default_tools)


def test_tool_policy_can_disable_tools_without_changing_default_contract():
    from nutrimaster.agent.tool_policy import ToolPolicy

    policy = ToolPolicy.default_user().with_disabled({"execute_shell"})

    assert "execute_shell" in ToolPolicy.default_user().default_tools
    assert "execute_shell" not in policy.enabled_tools()
    assert "read_tool" in policy.enabled_tools()
