"""
技能加载器 (Skill Loader)

与 my-skill-try/skill_loader.py 保持一致的命名和接口。

功能：
1. 扫描 skills/ 和 user_skills/ 目录下的 skill.md 文件，注册可用技能
2. 提供 skill CRUD 操作（创建/读取/更新/删除）
3. 基因名检测委托给 utils.gene_detection（向后兼容）

核心方法：
- list_dir(user_id)            → list  列出共享+用户私有 skill
- get_skill(name, user_id)     → Skill  获取技能详情
- load_skill(name, user_id)    → Skill  get_skill 别名
- save_skill(...)              → Skill  创建/更新 skill
- delete_skill(name, uid)      → bool   删除用户私有 skill
- has_gene_names(text)         → bool   检测文本中是否包含具体基因名（委托）
- extract_gene_names(text)     → list   提取文本中所有具体基因名（委托）
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# ---- 默认目录 ----
_DEFAULT_SKILLS_DIR = Path(__file__).parent
_DEFAULT_USER_SKILLS_DIR = Path(__file__).parent.parent / "user_skills"


@dataclass
class Skill:
    """技能元数据（从 skill.md 解析）"""
    name: str
    description: str
    content: str = ""
    tools: list[str] | str | None = field(default_factory=list)
    path: Path = field(default_factory=Path)
    is_shared: bool = True


class Skill_loader:
    """技能加载器：扫描 skill.md，注册技能，提供 CRUD。"""

    def __init__(
        self,
        skills_dir: Path | None = None,
        user_skills_dir: Path | None = None,
    ):
        self.skills_dir = Path(skills_dir) if skills_dir else _DEFAULT_SKILLS_DIR
        self.user_skills_dir = (
            Path(user_skills_dir) if user_skills_dir else _DEFAULT_USER_SKILLS_DIR
        )
        self._skills: dict[str, Skill] = {}
        self.load_skills()

    def __repr__(self):
        return f"Skill_loader(skills={list(self._skills.keys())})"

    # ------------------------------------------------------------------
    # 加载
    # ------------------------------------------------------------------

    def load_skills(self) -> dict[str, Skill]:
        """扫描 skills/ 目录，注册每个包含 skill.md 的子目录"""
        self._skills = {}
        if not self.skills_dir.exists():
            return self._skills

        for skill_file in sorted(self.skills_dir.glob("*/skill.md")):
            try:
                spec = self._load_skill_file(skill_file, is_shared=True)
                self._skills[spec.name] = spec
            except Exception:
                logger.warning("加载 skill 失败: %s", skill_file, exc_info=True)
        return dict(self._skills)

    def _load_user_skills(self, user_id: str) -> dict[str, Skill]:
        """加载指定用户的私有 skills"""
        user_dir = self.user_skills_dir / user_id
        if not user_dir.exists():
            return {}
        skills = {}
        for skill_file in sorted(user_dir.glob("*/skill.md")):
            try:
                spec = self._load_skill_file(skill_file, is_shared=False)
                skills[spec.name] = spec
            except Exception:
                logger.warning("加载用户 skill 失败: %s", skill_file, exc_info=True)
        return skills

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------

    def list_dir(self, user_id: str | None = None) -> list[Skill]:
        """列出共享 skill + 该用户的私有 skill"""
        all_skills = dict(self._skills)
        if user_id:
            user_skills = self._load_user_skills(user_id)
            all_skills.update(user_skills)
        return list(all_skills.values())

    def get_skill(self, name: str, user_id: str | None = None) -> Skill | None:
        """获取指定 skill（先查共享，再查用户私有）"""
        if name in self._skills:
            return self._skills[name]
        if user_id:
            user_skills = self._load_user_skills(user_id)
            return user_skills.get(name)
        return None

    def load_skill(self, name: str, user_id: str | None = None) -> Skill | None:
        """get_skill 的别名，与 my-skill-try 一致"""
        return self.get_skill(name, user_id)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def save_skill(
        self,
        name: str,
        content: str,
        user_id: str | None = None,
    ) -> Skill:
        """创建/更新 skill。user_id=None 写共享目录，否则写用户目录。"""
        if user_id:
            skill_dir = self.user_skills_dir / user_id / name
        else:
            skill_dir = self.skills_dir / name

        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "skill.md"
        skill_file.write_text(content, encoding="utf-8")

        spec = self._load_skill_file(skill_file, is_shared=(user_id is None))

        # 刷新缓存
        if user_id is None:
            self._skills[spec.name] = spec

        return spec

    def delete_skill(self, name: str, user_id: str) -> bool:
        """删除用户私有 skill（不允许删除共享 skill）"""
        skill_dir = self.user_skills_dir / user_id / name
        if not skill_dir.exists():
            return False

        import shutil
        shutil.rmtree(skill_dir)
        return True

    # ------------------------------------------------------------------
    # 基因名检测与提取（委托给 utils.gene_detection，保持向后兼容）
    # ------------------------------------------------------------------

    @staticmethod
    def has_gene_names(text: str) -> bool:
        """检测文本中是否包含具体的植物基因名"""
        from utils.gene_detection import has_gene_names
        return has_gene_names(text)

    @staticmethod
    def extract_gene_names(text: str) -> list[str]:
        """从文本中提取所有具体的植物基因名（去重，保持出现顺序）"""
        from utils.gene_detection import extract_gene_names
        return extract_gene_names(text)

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _load_skill_file(self, path: Path, is_shared: bool = True) -> Skill:
        """从 skill.md 解析技能元数据"""
        text = path.read_text(encoding="utf-8")
        meta = self._parse_front_matter(text)

        # 提取正文（去掉 frontmatter）
        content = text
        lines = text.splitlines()
        if lines and lines[0].strip() == "---":
            for idx in range(1, len(lines)):
                if lines[idx].strip() == "---":
                    content = "\n".join(lines[idx + 1:]).strip()
                    break

        name = meta.get("name") or path.parent.name
        description = meta.get("description", "")
        tools_raw = meta.get("tools", [])
        # 与 my-skill-try 一致：tools="all" 时设为 None 表示可用所有 tools
        if tools_raw == "all":
            tools = None
        elif isinstance(tools_raw, list):
            tools = tools_raw
        else:
            tools = []

        return Skill(
            name=name,
            description=description,
            content=content,
            tools=tools,
            path=path,
            is_shared=is_shared,
        )

    @staticmethod
    def _parse_front_matter(text: str) -> dict:
        """解析 skill.md 头部的 YAML-like front matter"""
        lines = text.splitlines()
        if len(lines) < 3 or lines[0].strip() != "---":
            return {}

        end_index = None
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                end_index = idx
                break

        if end_index is None:
            return {}

        raw_meta = lines[1:end_index]
        parsed: dict[str, object] = {}
        i = 0
        while i < len(raw_meta):
            line = raw_meta[i]
            if not line.strip() or ":" not in line:
                i += 1
                continue

            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            if value == ">":
                desc_lines: list[str] = []
                i += 1
                while i < len(raw_meta):
                    child = raw_meta[i]
                    if child.startswith("  "):
                        desc_lines.append(child.strip())
                        i += 1
                        continue
                    break
                parsed[key] = " ".join(desc_lines).strip()
                continue

            if value.startswith("[") and value.endswith("]"):
                items = [item.strip() for item in value[1:-1].split(",") if item.strip()]
                parsed[key] = items
            else:
                parsed[key] = value
            i += 1

        return parsed
