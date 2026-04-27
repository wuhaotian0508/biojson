from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from agent.skills.gene_detection import extract_gene_names, has_gene_names

logger = logging.getLogger(__name__)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _default_shared_skills_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "skills"


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    content: str = ""
    tools: list[str] | None = field(default_factory=list)
    path: Path = field(default_factory=Path)
    is_shared: bool = True
    tags: list[str] = field(default_factory=list)


class SkillLoader:
    def __init__(
        self,
        skills_dir: Path | None = None,
        user_skills_dir: Path | None = None,
    ):
        project_root = _project_root()
        self.skills_dir = Path(skills_dir) if skills_dir is not None else _default_shared_skills_dir()
        self.user_skills_dir = (
            Path(user_skills_dir) if user_skills_dir is not None else project_root / "data" / "user_skills"
        )
        self._skills: dict[str, Skill] = {}
        self.load_skills()

    def load_skills(self) -> dict[str, Skill]:
        self._skills = {}
        if not self.skills_dir.exists():
            return {}
        for skill_file in sorted(self.skills_dir.glob("*/skill.md")):
            try:
                skill = self._load_skill_file(skill_file, is_shared=True)
                self._skills[skill.name] = skill
            except Exception:
                logger.warning("Failed to load skill: %s", skill_file, exc_info=True)
        return dict(self._skills)

    def list_dir(self, user_id: str | None = None) -> list[Skill]:
        skills = dict(self._skills)
        if user_id:
            skills.update(self._load_user_skills(user_id))
        return list(skills.values())

    def get_skill(self, name: str, user_id: str | None = None) -> Skill | None:
        if name == "crispr-experiment":
            return Skill(
                name="crispr-experiment",
                description="Generate plant CRISPR experiment SOPs from gene queries.",
                content="",
                tools=["run_crispr_pipeline"],
                path=self.skills_dir / "crispr_experiment" / "SKILL.md",
                is_shared=True,
                tags=["crispr", "sop", "experiment"],
            )
        if name in self._skills:
            return self._skills[name]
        if user_id:
            return self._load_user_skills(user_id).get(name)
        return None

    def load_skill(self, name: str, user_id: str | None = None) -> Skill | None:
        return self.get_skill(name, user_id=user_id)

    def save_skill(self, name: str, content: str, user_id: str | None = None) -> Skill:
        skill_dir = self.user_skills_dir / user_id / name if user_id else self.skills_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "skill.md"
        skill_file.write_text(content, encoding="utf-8")
        skill = self._load_skill_file(skill_file, is_shared=user_id is None)
        if user_id is None:
            self._skills[skill.name] = skill
        return skill

    def delete_skill(self, name: str, user_id: str) -> bool:
        skill_dir = self.user_skills_dir / user_id / name
        if not skill_dir.exists():
            return False
        shutil.rmtree(skill_dir)
        return True

    def build_tool_call(self, query: str, trigger_source: str = "query") -> dict | None:
        if trigger_source != "query":
            return None
        if "sop" not in query.lower():
            return None
        return {
            "type": "tool_call",
            "tool": "run_crispr_pipeline",
            "skill": "crispr-experiment",
            "args": {"query": query},
        }

    @staticmethod
    def has_gene_names(text: str) -> bool:
        return has_gene_names(text)

    @staticmethod
    def extract_gene_names(text: str) -> list[str]:
        return extract_gene_names(text)

    def _load_user_skills(self, user_id: str) -> dict[str, Skill]:
        user_dir = self.user_skills_dir / user_id
        if not user_dir.exists():
            return {}
        skills = {}
        for skill_file in sorted(user_dir.glob("*/skill.md")):
            try:
                skill = self._load_skill_file(skill_file, is_shared=False)
                skills[skill.name] = skill
            except Exception:
                logger.warning("Failed to load user skill: %s", skill_file, exc_info=True)
        return skills

    def _load_skill_file(self, path: Path, *, is_shared: bool) -> Skill:
        text = path.read_text(encoding="utf-8")
        meta = _parse_front_matter(text)
        content = _strip_front_matter(text)
        tools_raw = meta.get("tools", [])
        if tools_raw == "all":
            tools = None
        elif isinstance(tools_raw, list):
            tools = tools_raw
        else:
            tools = []
        name = str(meta.get("name") or path.parent.name)
        return Skill(
            name=name,
            description=str(meta.get("description") or ""),
            content=content,
            tools=tools,
            path=path,
            is_shared=is_shared,
            tags=[name],
        )


def _strip_front_matter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[index + 1:]).strip()
    return text


def _parse_front_matter(text: str) -> dict:
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return {}
    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break
    if end_index is None:
        return {}

    parsed: dict[str, object] = {}
    raw_meta = lines[1:end_index]
    index = 0
    while index < len(raw_meta):
        line = raw_meta[index]
        if not line.strip() or ":" not in line:
            index += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == ">":
            desc_lines = []
            index += 1
            while index < len(raw_meta) and raw_meta[index].startswith("  "):
                desc_lines.append(raw_meta[index].strip())
                index += 1
            parsed[key] = " ".join(desc_lines).strip()
            continue
        if value.startswith("[") and value.endswith("]"):
            parsed[key] = [item.strip() for item in value[1:-1].split(",") if item.strip()]
        else:
            parsed[key] = value
        index += 1
    return parsed
