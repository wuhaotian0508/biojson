from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from agent.skills import extract_gene_names
from shared.llm import is_deepseek_reasoner

logger = logging.getLogger(__name__)

MAX_STEPS = 20
_SOP_SHORTCUT_RE = re.compile(r"(?i)\bsop\b|实验方案|crispr.*方案|基因编辑.*方案|生成.*方案|设计.*实验")


class Agent:
    """LLM-driven NutriMaster tool calling agent."""

    def __init__(self, registry, skill_loader, call_llm, call_llm_stream):
        self.registry = registry
        self.loader = skill_loader
        self.call_llm = call_llm
        self.call_llm_stream = call_llm_stream

    def _resolve_enabled_tools(
        self,
        user_id: str | None,
        use_depth: bool,
        use_personal: bool,
        skill_prefs: dict | None,
        tool_overrides: dict | None,
    ) -> set[str]:
        skill_prefs = skill_prefs or {}
        tool_overrides = tool_overrides or {}
        enabled: set[str] = set()

        for skill in self.loader.list_dir(user_id):
            pref = skill_prefs.get(skill.name, "auto")
            if pref == "disabled":
                continue
            skill_tools = skill.tools if skill.tools is not None else list(self.registry.tool_names)
            for tool_name in skill_tools:
                if tool_overrides.get(tool_name) == "disabled":
                    continue
                enabled.add(tool_name)

        for base_tool in ("read_tool", "write_tool", "execute_shell"):
            if base_tool in self.registry.tool_names:
                enabled.add(base_tool)

        if not use_personal and tool_overrides.get("personal_lib_search") != "enabled":
            enabled.discard("personal_lib_search")
        if not use_depth and tool_overrides.get("gene_db_search") != "enabled":
            enabled.discard("gene_db_search")

        for tool_name, override in tool_overrides.items():
            if override == "enabled" and tool_name in self.registry.tool_names:
                enabled.add(tool_name)
            elif override == "disabled":
                enabled.discard(tool_name)

        return enabled

    def _filter_tool_definitions(self, enabled_tools: set[str]) -> list[dict]:
        return [
            definition
            for definition in self.registry.get_definitions
            if definition["function"]["name"] in enabled_tools
        ]

    def _build_skill_xml(self, user_id: str | None = None, enabled_tools: set[str] | None = None) -> str:
        skills = self.loader.list_dir(user_id)
        if not skills:
            return ""
        lines = ["<available-skills>"]
        for skill in skills:
            if enabled_tools is not None and skill.tools is not None:
                active = [tool for tool in skill.tools if tool in enabled_tools]
                if not active:
                    continue
                tools = ", ".join(active)
            else:
                tools = ", ".join(skill.tools) if skill.tools else "all"
            lines.append(f'  <skill name="{skill.name}" path="{skill.path}" tools="{tools}">')
            lines.append(f"    {skill.description}")
            lines.append("  </skill>")
        lines.append("</available-skills>")
        return "\n".join(lines)

    def _build_tool_descriptions(self, enabled_tools: set[str] | None = None) -> str:
        lines = []
        for definition in self.registry.get_definitions:
            name = definition["function"]["name"]
            if enabled_tools and name not in enabled_tools:
                continue
            lines.append(f"- {name}: {definition['function'].get('description', '')}")
        return "\n".join(lines)

    def _build_system_prompt(
        self,
        user_id: str | None = None,
        use_depth: bool = False,
        use_personal: bool = False,
        enabled_tools: set[str] | None = None,
    ) -> str:
        return f"""你是一个专业的植物营养代谢生物学研究助手。

只有当问题涉及基因、蛋白质、代谢通路、文献检索、个人知识库或实验方案时才使用搜索工具。
普通问候、闲聊和通用解释直接回答。

{self._build_skill_xml(user_id, enabled_tools)}

可用工具：
{self._build_tool_descriptions(enabled_tools)}

回答要求：准确、聚焦、使用 Markdown；使用检索结果后在正文中用 [1] [2] 标注来源。"""

    @staticmethod
    def _msg_to_dict(msg, model_id: str = "") -> dict:
        if hasattr(msg, "model_dump"):
            data = msg.model_dump(exclude_none=True)
        elif isinstance(msg, dict):
            data = dict(msg)
        else:
            data = {
                key: getattr(msg, key)
                for key in ("role", "content", "tool_calls", "reasoning_content")
                if hasattr(msg, key) and getattr(msg, key) is not None
            }
        data.setdefault("role", "assistant")
        return data

    @staticmethod
    def _truncate_history(history: list, max_chars_per_msg: int = 800) -> list:
        truncated = []
        for msg in history or []:
            content = msg.get("content", "")
            if msg.get("role") == "assistant" and isinstance(content, str) and len(content) > max_chars_per_msg:
                truncated.append({**msg, "content": content[:max_chars_per_msg] + "\n...(之前回答已截断)"})
            else:
                truncated.append(msg)
        return truncated

    @staticmethod
    def _strip_reasoning_for_new_turn(messages: list[dict]) -> list[dict]:
        output = []
        for msg in messages:
            if msg.get("role") == "assistant" and "reasoning_content" in msg:
                output.append({key: value for key, value in msg.items() if key != "reasoning_content"})
            else:
                output.append(msg)
        return output

    @staticmethod
    def _extract_sources_from_tool_results(tool_results: list[dict]) -> list[dict]:
        sources = []
        for result in tool_results:
            tool_name = result.get("tool", "")
            content = result.get("content", "")
            blocks = re.split(r"\n\[(\d+)\]\s+", content)
            for index in range(1, len(blocks), 2):
                tool_index = int(blocks[index])
                block = blocks[index + 1] if index + 1 < len(blocks) else ""
                title = block.split("\n")[0].strip()
                source_type = "unknown"
                if tool_name == "pubmed_search" or "来源: PubMed" in block:
                    source_type = "pubmed"
                elif tool_name == "gene_db_search" or "来源: 基因数据库" in block:
                    source_type = "gene_db"
                elif tool_name == "personal_lib_search" or "来源: 个人知识库" in block:
                    source_type = "personal"
                pmid = re.search(r"PMID:\s*(\d+)", block)
                doi = re.search(r"DOI:\s*(\S+)", block)
                url = re.search(r"链接:\s*(https?://\S+)", block)
                journal = re.search(r"期刊:\s*(.+)", block)
                sources.append(
                    {
                        "source_type": source_type,
                        "title": title,
                        "paper_title": title,
                        "pmid": pmid.group(1) if pmid else "",
                        "doi": doi.group(1) if doi else "",
                        "url": url.group(1) if url else (f"https://doi.org/{doi.group(1)}" if doi else ""),
                        "journal": journal.group(1).strip() if journal else "",
                        "tool_index": tool_index,
                    }
                )
        return sources

    @staticmethod
    def _filter_cited_sources(answer_text: str, all_sources: list[dict]) -> list[dict]:
        cited = [int(match.group(1)) for match in re.finditer(r"\[(\d+)\]", answer_text)]
        output = []
        for number in cited:
            for source in all_sources:
                if source.get("tool_index") == number and source not in output:
                    output.append(source)
                    break
        return output

    def _is_reasoner_model(self, model_id: str) -> bool:
        return is_deepseek_reasoner(model_id or "")

    async def run(
        self,
        user_input: str,
        user_id: str | None = None,
        model_id: str = "",
        history: list | None = None,
        use_personal: bool = False,
        use_depth: bool = False,
        skill_prefs: dict | None = None,
        tool_overrides: dict | None = None,
    ):
        try:
            enabled_tools = self._resolve_enabled_tools(
                user_id=user_id,
                use_depth=use_depth,
                use_personal=use_personal,
                skill_prefs=skill_prefs,
                tool_overrides=tool_overrides,
            )
            yield {"type": "tools_enabled", "tools": sorted(enabled_tools)}

            tool_definitions = self._filter_tool_definitions(enabled_tools)
            messages = [
                {
                    "role": "system",
                    "content": self._build_system_prompt(user_id, use_depth, use_personal, enabled_tools),
                }
            ]
            messages.extend(self._truncate_history(history or []))
            messages.append({"role": "user", "content": user_input})
            messages = self._strip_reasoning_for_new_turn(messages)

            tool_results: list[dict] = []
            answer_text = ""
            for _step in range(MAX_STEPS):
                response = await self.call_llm(
                    messages,
                    tools=tool_definitions,
                    model_id=model_id,
                    is_agent_call=True,
                )
                assistant_message = self._msg_to_dict(response, model_id=model_id)
                messages.append(assistant_message)

                tool_calls = getattr(response, "tool_calls", None) or assistant_message.get("tool_calls") or []
                if not tool_calls:
                    answer_text = response.content if hasattr(response, "content") else assistant_message.get("content", "")
                    break

                for tool_call in tool_calls:
                    function = getattr(tool_call, "function", None) or tool_call.get("function", {})
                    tool_name = getattr(function, "name", None) or function.get("name")
                    raw_args = getattr(function, "arguments", None) or function.get("arguments") or "{}"
                    args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
                    if user_id and tool_name in {"personal_lib_search", "rag_search", "read_tool", "write_tool"}:
                        args.setdefault("user_id", user_id)
                    yield {"type": "tool_call", "tool": tool_name, "args": args}
                    try:
                        result = await self.registry.execute(tool_name, **args)
                    except Exception as exc:
                        result = f"工具执行失败: {exc}"
                    tool_results.append({"tool": tool_name, "content": str(result)})
                    yield {"type": "tool_result", "tool": tool_name, "summary": str(result)[:500]}
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": getattr(tool_call, "id", None) or tool_call.get("id", tool_name),
                            "name": tool_name,
                            "content": str(result),
                        }
                    )

            if answer_text:
                yield {"type": "text", "data": answer_text}
            sources = self._filter_cited_sources(
                answer_text,
                self._extract_sources_from_tool_results(tool_results),
            )
            if sources:
                yield {"type": "sources", "data": sources}
            genes = extract_gene_names(answer_text or user_input)
            if genes:
                yield {"type": "genes_available", "genes": genes}
            yield {"type": "done"}
        except Exception as exc:
            logger.exception("Agent run failed")
            yield {"type": "error", "data": str(exc)}


__all__ = ["Agent"]
