"""
技能加载器 (Skill Loader)

功能：
1. 扫描 skills/ 目录下的技能定义文件（SKILL.md），注册可用技能
2. 判断用户输入/LLM 回答是否应该触发某个技能（如 CRISPR 实验方案生成）
3. 从文本中检测/提取植物基因名

核心方法：
- has_gene_names(text)       → bool  检测文本中是否包含具体基因名
- extract_gene_names(text)   → list  提取文本中所有具体基因名（去重）
- should_trigger(...)        → bool  判断是否应触发指定技能
- build_tool_call(...)       → dict  构建技能调用参数
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import re


# ---- 默认技能目录（本文件所在目录） ----
_DEFAULT_SKILLS_DIR = Path(__file__).parent

# ---- 实验方案请求的关键词模式 ----
# 匹配用户希望获取实验方案/流程的意图
_EXPERIMENT_REQUEST_PATTERNS = (
    r"\bsop\b",
    r"\bprotocol\b",
    r"\bexperiment(?:al)? plan\b",
    r"\bexperimental design\b",
    r"实验方案",
    r"实验流程",
    r"实验设计",
    r"编辑方案",
    r"敲除方案",
    r"转化方案",
    r"设计.*方案",
)

# ---- SOP 专用触发模式（用于 query 自动触发，必须明确提到 "sop"） ----
# 匹配 sop / SOP / Sop 等任意大小写形式
# 注意：不使用 \b 词边界，因为 Python 的 \b 将中文字符视为 \w，
# 导致 "的sop" 中 "的" 和 "s" 之间无边界，匹配失败
_SOP_KEYWORD_PATTERN = re.compile(r"sop", re.IGNORECASE)

# ---- 基因编辑操作的关键词模式 ----
# 匹配基因编辑/敲除/过表达等操作相关表述
_GENE_EDITING_PATTERNS = (
    r"\bcrispr\b",
    r"\bknockout\b",
    r"\boverexpression\b",
    r"\bgene editing\b",
    r"基因编辑",
    r"敲除",
    r"过表达",
    r"遗传转化",
)

# ---- 植物基因名正则模式 ----
# 匹配格式：2 字母物种前缀 + 大写基因名 + 可选数字
# 示例：GmFAD2, AtMYB4, OsDREB1A, CrtB, SlMYB75
_GENE_NAME_RE = re.compile(r'\b[A-Z][a-z]{1,2}[A-Z][A-Za-z]{0,10}\d{0,3}[A-Za-z]?\b')

# ---- CRISPR 工具/酶名称黑名单（这些不是植物基因名） ----
_TOOL_NAME_BLACKLIST = {
    "SpCas9", "SaCas9", "FnCas12a", "LbCpf1", "AsCpf1",
    "CasRx", "dCas9", "nCas9", "Cas12a", "Cas13a",
}

# ---- 基因名后紧跟这些词表示泛指，不应视为具体基因 ----
# 示例："GmFAD2之类的" → 用户并未指定要编辑 GmFAD2
_VAGUE_SUFFIXES = ("之类", "之类的", "等", "等等", "类似")


@dataclass(frozen=True)
class SkillSpec:
    """技能元数据（从 SKILL.md 文件解析得到）"""
    name: str           # 技能唯一标识，如 "crispr-experiment"
    description: str    # 技能描述
    tags: tuple[str, ...]  # 标签列表
    path: Path          # SKILL.md 文件路径


class SkillLoader:
    """
    技能加载器：扫描技能目录，注册技能，判断触发条件。
    """

    def __init__(self, skills_dir: Path | None = None):
        self.skills_dir = Path(skills_dir) if skills_dir else _DEFAULT_SKILLS_DIR
        self._skills: dict[str, SkillSpec] = {}
        self.load_skills()

    def load_skills(self) -> dict[str, SkillSpec]:
        """扫描 skills 目录，注册每个包含 SKILL.md 的子目录为一个技能"""
        self._skills = {}
        if not self.skills_dir.exists():
            return self._skills

        for skill_file in self.skills_dir.glob("*/SKILL.md"):
            spec = self._load_skill_file(skill_file)
            self._skills[spec.name] = spec
        return dict(self._skills)

    def list_skills(self) -> Iterable[SkillSpec]:
        """列出所有已注册技能"""
        return self._skills.values()

    def get_skill(self, name: str) -> SkillSpec:
        """按名称获取技能元数据"""
        try:
            return self._skills[name]
        except KeyError as exc:
            raise ValueError(f"未知技能: {name}") from exc

    # ------------------------------------------------------------------
    # 基因名检测与提取
    # ------------------------------------------------------------------

    @staticmethod
    def has_gene_names(text: str) -> bool:
        """
        检测文本中是否包含具体的植物基因名。

        排除规则：
        1. CRISPR 工具名（SpCas9 等）不算基因名
        2. 基因名后紧跟"之类/等"等模糊后缀时不算具体基因

        参数:
            text: 待检测文本

        返回:
            True 如果检测到至少一个具体基因名
        """
        for m in _GENE_NAME_RE.finditer(text):
            name = m.group()
            # 跳过 CRISPR 工具名
            if name in _TOOL_NAME_BLACKLIST:
                continue
            # 跳过后跟模糊后缀的情况（如 "GmFAD2之类"）
            after = text[m.end():]
            if any(after.startswith(s) for s in _VAGUE_SUFFIXES):
                continue
            return True
        return False

    @staticmethod
    def extract_gene_names(text: str) -> list[str]:
        """
        从文本中提取所有具体的植物基因名（去重，保持出现顺序）。

        使用与 has_gene_names() 相同的正则和排除逻辑，
        但返回所有匹配的基因名列表，而非仅判断是否存在。

        参数:
            text: 待提取文本（通常是 LLM 回答全文）

        返回:
            去重的基因名列表，如 ["GmFAD2", "AtMYB4", "OsNAS2"]
        """
        seen = set()         # 用于去重
        gene_names = []      # 保持出现顺序

        for m in _GENE_NAME_RE.finditer(text):
            name = m.group()
            # ---- 跳过 CRISPR 工具名 ----
            if name in _TOOL_NAME_BLACKLIST:
                continue
            # ---- 跳过后跟模糊后缀的情况 ----
            after = text[m.end():]
            if any(after.startswith(s) for s in _VAGUE_SUFFIXES):
                continue
            # ---- 去重并收集 ----
            if name not in seen:
                seen.add(name)
                gene_names.append(name)

        return gene_names

    # ------------------------------------------------------------------
    # 技能触发判断
    # ------------------------------------------------------------------

    def should_trigger(
        self,
        *,
        query: str = "",
        answer_text: str = "",
        trigger_source: str = "query",
        skill_name: str = "crispr-experiment",
    ) -> bool:
        """
        判断是否应触发指定技能。

        触发条件根据 trigger_source 不同而有差异：

        - "button"（按钮触发）: 始终返回 True，无需任何条件检查
        - "query"（用户输入触发）: 需同时满足以下 3 个条件：
            1. 文本中明确包含 "sop"（不区分大小写：sop/SOP/Sop 均可）
            2. 文本中提到基因编辑操作（CRISPR/敲除/过表达 等）
            3. 文本中包含具体的植物基因名（排除工具名和泛指表述）
        - 其他来源: 需满足实验方案请求 + 基因编辑操作两个条件

        参数:
            query: 用户的输入查询
            answer_text: LLM 生成的回答
            trigger_source: 触发来源（"query" / "button" / 其他）
            skill_name: 技能名称

        返回:
            True 如果应该触发该技能
        """
        # 确认技能存在
        self.get_skill(skill_name)

        # ---- 按钮触发：始终通过 ----
        if trigger_source == "button":
            return True

        # ---- 合并查询和回答文本进行检测 ----
        text = f"{query}\n{answer_text}".strip()
        if not text:
            return False

        normalized = text.lower()

        # ---- 检查是否为基因编辑相关任务 ----
        is_editing_task = any(
            re.search(pattern, normalized, flags=re.IGNORECASE)
            for pattern in _GENE_EDITING_PATTERNS
        )

        # ---- query 触发：只需要用户明确提到 "sop" ----
        # 基因名由后续 LLM 提取，不在这里用正则判断
        # （正则无法匹配 Shrunken-2、Opaque-2 等非 CamelCase 基因名）
        if trigger_source == "query":
            has_sop = bool(_SOP_KEYWORD_PATTERN.search(query))
            return has_sop

        # ---- 其他触发来源：实验方案请求 + 基因编辑操作 ----
        wants_plan = any(
            re.search(pattern, normalized, flags=re.IGNORECASE)
            for pattern in _EXPERIMENT_REQUEST_PATTERNS
        )
        return wants_plan and is_editing_task

    def build_tool_call(
        self,
        *,
        query: str = "",
        answer_text: str = "",
        genes: list[dict] | None = None,
        trigger_source: str = "query",
        skill_name: str = "crispr-experiment",
    ) -> dict | None:
        """
        构建技能调用参数。

        先调用 should_trigger() 判断是否应触发，若通过则构建
        包含查询、回答文本、基因列表等信息的调用参数字典。

        参数:
            query: 用户输入
            answer_text: LLM 回答
            genes: 预先提取的基因列表（可选）
            trigger_source: 触发来源
            skill_name: 技能名称

        返回:
            调用参数字典，或 None（不应触发时）
        """
        if not self.should_trigger(
            query=query,
            answer_text=answer_text,
            trigger_source=trigger_source,
            skill_name=skill_name,
        ):
            return None

        spec = self.get_skill(skill_name)
        args = {
            "query": query,
            "answer_text": answer_text,
            "trigger_source": trigger_source,
        }
        if genes:
            args["genes"] = genes

        return {
            "type": "tool_call",
            "tool": "run_crispr_pipeline",
            "skill": spec.name,
            "args": args,
        }

    # ------------------------------------------------------------------
    # 内部方法：解析 SKILL.md 文件
    # ------------------------------------------------------------------

    def _load_skill_file(self, path: Path) -> SkillSpec:
        """从 SKILL.md 文件中解析技能元数据"""
        text = path.read_text(encoding="utf-8")
        meta = self._parse_front_matter(text)
        name = meta.get("name") or path.parent.name
        description = meta.get("description", "")
        tags = tuple(meta.get("tags", []))
        return SkillSpec(
            name=name,
            description=description,
            tags=tags,
            path=path,
        )

    @staticmethod
    def _parse_front_matter(text: str) -> dict:
        """
        解析 SKILL.md 文件头部的 YAML-like front matter。

        支持格式：
        ---
        name: skill-name
        description: >
          多行描述文本
        tags: [tag1, tag2]
        ---
        """
        lines = text.splitlines()
        if len(lines) < 3 or lines[0].strip() != "---":
            return {}

        # 查找结束标记 ---
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

            # 处理多行描述（以 > 标记开头）
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

            # 处理数组格式 [item1, item2]
            if value.startswith("[") and value.endswith("]"):
                items = [item.strip() for item in value[1:-1].split(",") if item.strip()]
                parsed[key] = items
            else:
                parsed[key] = value
            i += 1

        return parsed
