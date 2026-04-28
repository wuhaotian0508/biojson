from __future__ import annotations

from typing import Any


class PromptBuilder:
    def __init__(self, skill_loader: Any | None = None):
        self.skill_loader = skill_loader

    def build(self, *, user_id: str | None = None, use_depth: bool = False, use_personal: bool = False) -> str:
        mode = "深度搜索" if use_depth else "普通搜索"
        personal = "开启" if use_personal else "关闭"
        return f"""你是 NutriMaster，一个专业的植物营养代谢生物学研究助手。

当前模式：{mode}
个人库：{personal}

工具使用规则：
1. 普通问候、闲聊、简单说明不要调用工具。
2. 涉及基因、蛋白、代谢通路、作物营养、文献证据的问题，优先调用 rag_search。
3. rag_search 是复合 RAG 工具；只要调用它，内部会同时检索 PubMed 摘要和本地基因库。
4. 用户明确要求实验设计、CRISPR、SOP、敲除/过表达实验方案时，调用 experiment_design。
5. 不要臆造引用。使用 rag_search 返回的证据时，正文必须使用证据中的 [编号]。

回答要求：
- 使用中文 Markdown。
- 结论先行，必要时分点说明。
- 对不确定的结论标明证据不足或需要进一步实验验证。

{self._skills_block(user_id)}
"""

    def _skills_block(self, user_id: str | None) -> str:
        if self.skill_loader is None:
            return ""
        skills = self.skill_loader.list_dir(user_id)
        if not skills:
            return ""
        lines = ["后台 skills 提示："]
        for skill in skills:
            lines.append(f"- {skill.name}: {skill.description}")
            if skill.content:
                lines.append(skill.content[:1200])
        return "\n".join(lines)
