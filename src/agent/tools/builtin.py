from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path

from agent.tools.base import BaseTool


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class FileAccessPolicy:
    skills_dir: Path
    user_skills_dir: Path
    readonly_skill_creator_dir: Path | None = None

    @classmethod
    def default(cls) -> "FileAccessPolicy":
        skills_dir = Path(__file__).resolve().parents[2] / "skills"
        user_skills_dir = _project_root() / "data" / "user_skills"
        return cls(
            skills_dir=skills_dir,
            user_skills_dir=user_skills_dir,
            readonly_skill_creator_dir=skills_dir / "skill-creator",
        )

    def check_path(self, file_path: str | Path, *, write: bool = False, user_id: str | None = None) -> Path:
        real = Path(file_path).expanduser().resolve()
        skills_dir = self.skills_dir.resolve()
        user_skills_dir = self.user_skills_dir.resolve()
        in_skills = _is_relative_to(real, skills_dir)
        in_user_skills = _is_relative_to(real, user_skills_dir)
        if not in_skills and not in_user_skills:
            raise PermissionError(f"Path outside allowed skill directories: {file_path}")
        if in_user_skills:
            if not user_id:
                raise PermissionError(f"User identity required for user skill access: {file_path}")
            user_dir = (user_skills_dir / user_id).resolve()
            if not _is_relative_to(real, user_dir):
                raise PermissionError(f"Cannot access another user's skill files: {file_path}")
        if write and self.readonly_skill_creator_dir is not None:
            creator_dir = self.readonly_skill_creator_dir.resolve()
            if _is_relative_to(real, creator_dir):
                raise PermissionError(f"Cannot write to readonly skill creator directory: {file_path}")
        return real


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


class ReadTool(BaseTool):
    name = "read_tool"
    description = "read 文件"

    def __init__(self, *, policy: FileAccessPolicy | None = None):
        self.policy = policy or FileAccessPolicy.default()

    @property
    def schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "要读的文件的完整路径",
                        }
                    },
                    "required": ["file_path"],
                },
            },
        }

    async def execute(self, file_path, timeout=None, user_id=None, **_):
        checked_path = self.policy.check_path(file_path, user_id=user_id)
        return checked_path.read_text(encoding="utf-8")


class WriteTool(BaseTool):
    name = "write_tool"
    description = "write 文件"

    def __init__(self, *, policy: FileAccessPolicy | None = None):
        self.policy = policy or FileAccessPolicy.default()

    @property
    def schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "要写的文件的完整路径",
                        },
                        "content": {
                            "type": "string",
                            "description": "要写的内容",
                        },
                    },
                    "required": ["file_path", "content"],
                },
            },
        }

    async def execute(self, file_path, content, timeout=None, user_id=None, **_):
        checked_path = self.policy.check_path(file_path, write=True, user_id=user_id)
        checked_path.parent.mkdir(parents=True, exist_ok=True)
        checked_path.write_text(content, encoding="utf-8")
        return content


class ShellTool(BaseTool):
    name = "execute_shell"
    description = "执行 shell 命令"

    @property
    def schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "要执行的 shell 命令",
                        }
                    },
                    "required": ["command"],
                },
            },
        }

    async def execute(self, command, timeout=None, **_):
        if ".." in command:
            raise PermissionError("Command cannot reference parent directory")
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd(),
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout or 60)
        output = stdout.decode()
        if stderr:
            output += f"\nSTDERR:\n{stderr.decode()}"
        output += f"\nExit code: {process.returncode}"
        return output
