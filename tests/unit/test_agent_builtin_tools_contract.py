from __future__ import annotations

import asyncio


def test_read_and_write_tools_use_explicit_file_policy(tmp_path):
    from nutrimaster.agent.tools.builtin import FileAccessPolicy, ReadTool, WriteTool

    skills_dir = tmp_path / "skills"
    user_skills_dir = tmp_path / "user_skills"
    allowed_file = user_skills_dir / "user-1" / "note.md"
    allowed_file.parent.mkdir(parents=True)

    policy = FileAccessPolicy(skills_dir=skills_dir, user_skills_dir=user_skills_dir)
    write_tool = WriteTool(policy=policy)
    read_tool = ReadTool(policy=policy)

    assert asyncio.run(
        write_tool.execute(
            file_path=str(allowed_file),
            content="hello",
            user_id="user-1",
        )
    ) == "hello"
    assert asyncio.run(read_tool.execute(file_path=str(allowed_file), user_id="user-1")) == "hello"


def test_file_policy_rejects_paths_outside_allowed_roots(tmp_path):
    from nutrimaster.agent.tools.builtin import FileAccessPolicy, ReadTool

    policy = FileAccessPolicy(
        skills_dir=tmp_path / "skills",
        user_skills_dir=tmp_path / "user_skills",
    )

    try:
        asyncio.run(ReadTool(policy=policy).execute(file_path=str(tmp_path / "secret.txt")))
    except PermissionError as exc:
        assert "outside allowed skill directories" in str(exc)
    else:
        raise AssertionError("Expected PermissionError")


def test_shell_tool_rejects_parent_directory_escape():
    from nutrimaster.agent.tools.builtin import ShellTool

    try:
        asyncio.run(ShellTool().execute(command="ls .."))
    except PermissionError as exc:
        assert "parent directory" in str(exc)
    else:
        raise AssertionError("Expected PermissionError")
