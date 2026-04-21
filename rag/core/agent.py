"""
Agent — LLM 驱动的工具调用循环（替代 pipeline.py + generator.py）

核心逻辑：
  1. 构建系统提示（可用技能列表 + 工具描述 + 行为指令）
  2. 用户消息 → LLM → 工具调用 → 结果注入 → 循环
  3. 最终文本流式输出，通过 SSE 事件推送给前端

工具/技能过滤：
  - 普通模式：只提供 skill 声明的工具子集
  - 深度模式：提供更多工具（gene_db_search 等）
  - use_personal=False 时不暴露 personal_lib_search
  - skill_prefs / tool_overrides 允许用户手动开关

事件类型（async generator yield）：
  - skill_selected  : agent 选择了某个技能
  - tool_call       : agent 调用了某个工具
  - tool_result     : 工具返回结果摘要
  - text            : 流式回答文本 chunk
  - done            : 完成
  - error           : 错误
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path

from core.context import ContextManager
from utils.gene_detection import extract_gene_names

logger = logging.getLogger(__name__)

MAX_STEPS = 20

# SOP 快捷路径关键词正则（匹配用户输入中包含 SOP/实验方案 相关意图的查询）
_SOP_SHORTCUT_RE = re.compile(
    r"(?i)\bsop\b|实验方案|crispr.*方案|基因编辑.*方案|生成.*方案|设计.*实验"
)

# 检测模型把 function call 写进 content 文本的正则（用于过滤流式输出）
_FUNC_CALL_LEAK_RE = re.compile(
    r'^\s*\{?\s*"(?:name|function|tool_calls?|arguments)"', re.MULTILINE
)


class Agent:
    """LLM 工具调用 Agent（替代 RAGPipeline + RAGGenerator）"""

    def __init__(self, registry, skill_loader, call_llm, call_llm_stream):
        """
        参数:
            registry:        Toolregistry 实例
            skill_loader:    Skill_loader 实例
            call_llm:        async def call_llm(messages, tools, model_id, **kw) -> message
            call_llm_stream: async generator call_llm_stream(messages, model_id, **kw) -> chunks
        """
        self.registry = registry
        self.loader = skill_loader
        self.call_llm = call_llm
        self.call_llm_stream = call_llm_stream
        self.context_mgr = ContextManager(call_llm_for_summary=call_llm)

    # ------------------------------------------------------------------
    # 工具/技能过滤
    # ------------------------------------------------------------------
    def _resolve_enabled_tools(
        self,
        user_id: str | None,
        use_depth: bool,
        use_personal: bool,
        skill_prefs: dict | None,
        tool_overrides: dict | None,
    ) -> set[str]:
        """根据模式、skill_prefs、tool_overrides 确定本次启用的工具集合。

        规则：
        - 遍历用户可见的 skills，收集其 tools 列表
        - skill_prefs: skill_name -> "must_use" / "disabled" / "auto"
        - tool_overrides: tool_name -> "enabled" / "disabled" / "auto"
        - use_personal=False → 移除 personal_lib_search
        - use_depth=False → 移除 gene_db_search（普通模式不深度检索基因库）
        - read_tool / write_tool / execute_shell 始终可用（供 skill-creator 等使用）
        """
        skill_prefs = skill_prefs or {}
        tool_overrides = tool_overrides or {}

        skills = self.loader.list_dir(user_id)
        enabled: set[str] = set()

        for skill in skills:
            pref = skill_prefs.get(skill.name, "auto")
            if pref == "disabled":
                continue
            # tools=None 表示 "all"
            skill_tools = (
                skill.tools if skill.tools is not None
                else list(self.registry.tool_names)
            )
            for tool_name in skill_tools:
                override = tool_overrides.get(tool_name, "auto")
                if override == "disabled":
                    continue
                if pref == "must_use" or override == "enabled":
                    enabled.add(tool_name)
                else:
                    enabled.add(tool_name)

        # 基础工具始终可用
        for base_tool in ("read_tool", "write_tool", "execute_shell"):
            if base_tool in self.registry.tool_names:
                enabled.add(base_tool)

        # 条件过滤（显式 override "enabled" 可以覆盖模式限制）
        if not use_personal and tool_overrides.get("personal_lib_search") != "enabled":
            enabled.discard("personal_lib_search")
        if not use_depth and tool_overrides.get("gene_db_search") != "enabled":
            enabled.discard("gene_db_search")

        return enabled

    def _filter_tool_definitions(self, enabled_tools: set[str]) -> list[dict]:
        """从 registry 取所有 schema，只保留 enabled_tools 中的。"""
        return [
            td for td in self.registry.get_definitions
            if td["function"]["name"] in enabled_tools
        ]

    # ------------------------------------------------------------------
    # 系统提示构建
    # ------------------------------------------------------------------
    def _build_skill_xml(
        self,
        user_id: str | None = None,
        enabled_tools: set[str] | None = None,
    ) -> str:
        """构建 <available-skills> XML 片段，只展示有可用工具的 skills"""
        skills = self.loader.list_dir(user_id)
        if not skills:
            return ""

        lines = ["<available-skills>"]
        for skill in skills:
            # 如果 skill 的所有工具都被禁用，就不展示该 skill
            if enabled_tools is not None and skill.tools is not None:
                active = [t for t in skill.tools if t in enabled_tools]
                if not active:
                    continue
                tools_str = ", ".join(active)
            else:
                tools_str = ", ".join(skill.tools) if skill.tools else "all"

            lines.append(f'  <skill name="{skill.name}" path="{skill.path}" tools="{tools_str}">')
            lines.append(f"    {skill.description}")
            lines.append("  </skill>")
        lines.append("</available-skills>")
        return "\n".join(lines)

    def _build_tool_descriptions(self, enabled_tools: set[str] | None = None) -> str:
        """构建工具名称+描述列表（仅 enabled 的工具）"""
        lines = []
        for tool_def in self.registry.get_definitions:
            name = tool_def["function"]["name"]
            if enabled_tools and name not in enabled_tools:
                continue
            desc = tool_def["function"].get("description", "")
            lines.append(f"- {name}: {desc}")
        return "\n".join(lines)

    def _build_system_prompt(
        self,
        user_id: str | None = None,
        use_depth: bool = False,
        use_personal: bool = False,
        enabled_tools: set[str] | None = None,
    ) -> str:
        """构建完整系统提示"""
        skill_xml = self._build_skill_xml(user_id, enabled_tools)
        tool_desc = self._build_tool_descriptions(enabled_tools)

        depth_instruction = ""
        if use_depth:
            depth_instruction = (
                "\n\n## 深度调研模式\n"
                "用户开启了深度调研模式，请：\n"
                "1. 同时使用 pubmed_search 和 gene_db_search 工具，检索更全面的信息\n"
                "2. 撰写系统性的综合分析报告，包括：概述、关键基因分析、代谢通路、调控网络、总结\n"
                "3. 使用表格汇总和对比基因信息\n"
                "4. 分析基因间的关联和调控关系\n"
                "5. 可以多次搜索不同关键词以获取更全面的信息\n"
            )

        personal_instruction = ""
        if use_personal:
            personal_instruction = (
                "\n\n## 个人知识库\n"
                "用户开启了个人知识库搜索，请在适当时候使用 personal_lib_search 工具"
                "搜索用户上传的文献。\n"
            )

        return f"""\
你是一个专业的植物分子生物学研究助手，拥有搜索工具和技能系统。

## 工具使用原则（严格遵守）

**当且仅当**用户的问题涉及以下内容时，才使用搜索工具（rag_search、pubmed_search、gene_db_search、personal_lib_search）：
- 基因、蛋白质、酶、转运体、转录因子、代谢通路、表型等分子生物学概念
- 文献检索、论文查询、PubMed 搜索
- 实验方案设计（如 CRISPR 基因编辑）
- 需要查阅用户个人知识库中的文档

**当且仅当**用户明确要求创建、修改、管理技能时，才读取 skill.md 文件。

其他所有情况（问候、闲聊、感谢、解释概念、通用问答等），**直接回答，不调用任何工具。**

{skill_xml}

当用户请求与某个技能匹配、且确实需要执行该技能的完整工作流时，
先用 read_tool 读取该技能文件的完整内容（路径在上方 XML 中），然后按照技能指令操作。

## 可用工具
{tool_desc}

## 回答要求（仅在使用搜索工具后适用）
1. **准确性**: 只使用工具检索到的信息，不要编造
2. **结构化**: 使用 Markdown 格式，包括标题、列表、表格、加粗等
3. **来源标注**: 在正文中用 [1] [2] 等标注信息来源
4. **专业性**: 使用准确的专业术语
5. **不要在末尾列参考文献**: 系统会自动附上参考文献列表
6. **不要加免责声明**: 不要加入"检索结果不足"之类的声明{depth_instruction}{personal_instruction}"""

    # ------------------------------------------------------------------
    # 从工具结果中提取来源信息
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_sources_from_tool_results(tool_results: list[dict]) -> list[dict]:
        """从工具调用结果中提取参考文献来源（PubMed、gene_db 等）。

        解析 pubmed_search 返回的格式化文本，提取 title/PMID/journal/url。
        解析 gene_db_search 返回的格式化文本，提取 title/DOI。

        返回格式：每个 source 包含 tool_index 字段，表示在工具输出中的原始编号
        """
        sources = []

        for tr in tool_results:
            tool_name = tr.get("tool", "")
            content = tr.get("content", "")

            if tool_name == "pubmed_search":
                # 解析 PubMed 格式化输出
                # [1] Title here
                #     期刊: Journal Name
                #     PMID: 12345678
                #     链接: https://pubmed.ncbi.nlm.nih.gov/12345678/
                blocks = re.split(r'\n\[(\d+)\]\s+', content)
                # blocks[0] = header, then alternating: number, block_text
                for i in range(1, len(blocks), 2):
                    tool_index = blocks[i]  # 原始编号
                    block = blocks[i + 1] if i + 1 < len(blocks) else ""
                    title_line = block.split('\n')[0].strip()
                    pmid_match = re.search(r'PMID:\s*(\d+)', block)
                    url_match = re.search(r'链接:\s*(https?://\S+)', block)
                    journal_match = re.search(r'期刊:\s*(.+)', block)
                    sources.append({
                        "source_type": "pubmed",
                        "title": title_line,
                        "paper_title": title_line,
                        "pmid": pmid_match.group(1) if pmid_match else "",
                        "url": url_match.group(1) if url_match else "",
                        "journal": journal_match.group(1).strip() if journal_match else "",
                        "doi": "",
                        "tool_index": int(tool_index),  # 保存原始编号
                    })

            elif tool_name == "gene_db_search":
                # 解析 gene_db_search 格式化输出
                # [1] GeneName (type) | Journal | DOI: xxx
                blocks = re.split(r'\n\[(\d+)\]\s+', content)
                for i in range(1, len(blocks), 2):
                    tool_index = blocks[i]
                    block = blocks[i + 1] if i + 1 < len(blocks) else ""
                    first_line = block.split('\n')[0].strip()
                    doi_match = re.search(r'DOI:\s*(\S+)', block)
                    sources.append({
                        "source_type": "gene_db",
                        "title": first_line,
                        "paper_title": first_line,
                        "doi": doi_match.group(1) if doi_match else "",
                        "url": f"https://doi.org/{doi_match.group(1)}" if doi_match else "",
                        "pmid": "",
                        "tool_index": int(tool_index),
                    })

            elif tool_name == "personal_lib_search":
                # 解析 personal_lib_search 格式化输出
                blocks = re.split(r'\n\[(\d+)\]\s+', content)
                for i in range(1, len(blocks), 2):
                    tool_index = blocks[i]
                    block = blocks[i + 1] if i + 1 < len(blocks) else ""
                    first_line = block.split('\n')[0].strip()
                    sources.append({
                        "source_type": "personal",
                        "title": first_line,
                        "filename": first_line,
                        "url": "",
                        "doi": "",
                        "pmid": "",
                        "tool_index": int(tool_index),
                    })

            elif tool_name == "rag_search":
                # 解析 rag_search 综合搜索输出
                # [1] Title
                #     来源: PubMed/基因数据库/个人知识库
                #     期刊/PMID/DOI 等元数据
                blocks = re.split(r'\n\[(\d+)\]\s+', content)
                for i in range(1, len(blocks), 2):
                    tool_index = blocks[i]
                    block = blocks[i + 1] if i + 1 < len(blocks) else ""
                    lines = block.split('\n')
                    title_line = lines[0].strip()

                    # 检测来源类型
                    source_type = "unknown"
                    if "来源: PubMed" in block:
                        source_type = "pubmed"
                    elif "来源: 基因数据库" in block:
                        source_type = "gene_db"
                    elif "来源: 个人知识库" in block:
                        source_type = "personal"

                    # 提取元数据
                    pmid_match = re.search(r'PMID:\s*(\d+)', block)
                    doi_match = re.search(r'DOI:\s*(\S+)', block)
                    url_match = re.search(r'链接:\s*(https?://\S+)', block)
                    journal_match = re.search(r'期刊:\s*(.+)', block)

                    source_dict = {
                        "source_type": source_type,
                        "title": title_line,
                        "paper_title": title_line,
                        "pmid": pmid_match.group(1) if pmid_match else "",
                        "doi": doi_match.group(1) if doi_match else "",
                        "url": url_match.group(1) if url_match else "",
                        "journal": journal_match.group(1).strip() if journal_match else "",
                        "tool_index": int(tool_index),
                    }

                    # 如果是个人知识库，提取文件名
                    if source_type == "personal":
                        source_dict["filename"] = title_line

                    sources.append(source_dict)

        return sources

    @staticmethod
    def _filter_cited_sources(answer_text: str, all_sources: list[dict]) -> list[dict]:
        """从回答文本中提取实际引用的编号，过滤并重排 sources 列表。

        Args:
            answer_text: LLM 生成的回答文本，包含 [1], [2] 等引用标记
            all_sources: 从工具结果提取的所有来源，每个包含 tool_index 字段

        Returns:
            按引用顺序排列的 sources 列表，只包含实际被引用的文献
        """
        # 提取回答中所有的引用编号 [N]
        cited_numbers = set()
        for match in re.finditer(r'\[(\d+)\]', answer_text):
            cited_numbers.add(int(match.group(1)))

        if not cited_numbers:
            # 如果没有引用，返回空列表（不显示参考文献）
            return []

        # 按 tool_index 匹配，保留被引用的文献
        cited_sources = []
        for num in sorted(cited_numbers):
            for source in all_sources:
                if source.get("tool_index") == num:
                    cited_sources.append(source)
                    break

        return cited_sources

    # ------------------------------------------------------------------
    # 消息序列化（处理 DeepSeek reasoner 的 reasoning_content）
    # ------------------------------------------------------------------
    @staticmethod
    def _msg_to_dict(msg, model_id: str = "") -> dict:
        """将 LLM 返回的 message 对象转为 dict，追加到 messages 列表。

        DeepSeek reasoner 在同一轮工具调用循环内，必须回传 reasoning_content，
        否则 API 会返回 400 错误。
        """
        # openai SDK 的 message 对象可以直接 model_dump
        if hasattr(msg, "model_dump"):
            d = msg.model_dump(exclude_none=True)
        else:
            d = dict(msg) if not isinstance(msg, dict) else msg

        # 确保基本字段存在
        d.setdefault("role", "assistant")
        return d

    def _is_reasoner_model(self, model_id: str) -> bool:
        """判断当前 model_id 解析出的模型是否为 DeepSeek reasoner。"""
        _, model_name = _resolve_async_client(model_id)
        return is_deepseek_reasoner(model_name)

    @staticmethod
    def _strip_reasoning_for_new_turn(messages: list[dict]) -> list[dict]:
        """新一轮用户提问前，移除旧 assistant 消息中的 reasoning_content。

        DeepSeek 文档建议：新问题开始时移除旧 reasoning_content，
        API 即使收到也会忽略，但移除可以节省 token。
        """
        result = []
        for msg in messages:
            if msg.get("role") == "assistant" and "reasoning_content" in msg:
                cleaned = {k: v for k, v in msg.items() if k != "reasoning_content"}
                result.append(cleaned)
            else:
                result.append(msg)
        return result

    # ------------------------------------------------------------------
    # 历史消息截断
    # ------------------------------------------------------------------
    @staticmethod
    def _truncate_history(history: list, max_chars_per_msg: int = 800) -> list:
        """截断历史消息，避免 context 过长。"""
        if not history:
            return []
        truncated = []
        for msg in history:
            if msg.get("role") == "assistant" and len(msg.get("content", "")) > max_chars_per_msg:
                content = msg["content"][:max_chars_per_msg] + "\n...(之前回答已截断)"
                truncated.append({"role": "assistant", "content": content})
            else:
                truncated.append(msg)
        return truncated

    # ------------------------------------------------------------------
    # SOP 快捷路径
    # ------------------------------------------------------------------
    async def _run_sop_shortcut(
        self,
        user_input: str,
        history: list | None,
        model_id: str,
    ):
        """当用户输入包含 SOP 关键词时，跳过所有工具调用，
        直接用 LLM 提取基因 → NCBI 验证 → 返回验证结果供前端确认。"""
        from skills.crispr_experiment.pipeline import ExperimentPipeline
        from skills.crispr_experiment.gene2accession import (
            _search_gene_ids, _normalize_species_name,
        )
        from Bio import Entrez

        exp_pipeline = ExperimentPipeline()
        try:
            # 1. 构建上下文文本（用户输入 + 历史对话）
            context_parts = []
            if history:
                for msg in history[-4:]:  # 最近2轮对话
                    context_parts.append(msg.get("content", ""))
            context_parts.append(user_input)
            source_text = "\n".join(context_parts)

            # 2. LLM 提取基因
            yield {"type": "sop_extracting", "data": "正在从对话中提取基因..."}
            try:
                genes = await asyncio.to_thread(
                    exp_pipeline.extract_genes_with_llm, source_text
                )
            except ValueError:
                # 未提取到基因，回退到正常文本回答
                yield {"type": "text", "data": "未能从您的描述中提取到具体的基因信息，请提供更详细的基因名称和物种信息。"}
                yield {"type": "done"}
                return

            yield {"type": "sop_genes_extracted", "genes": genes}

            # 3. NCBI 验证
            yield {"type": "sop_ncbi_verifying", "data": "正在 NCBI 确认基因信息..."}
            Entrez.email = "biojson_rag@example.com"
            verified = []
            for g in genes:
                species = await asyncio.to_thread(
                    _normalize_species_name, g.get("species", "")
                )
                gene_ids = await asyncio.to_thread(
                    _search_gene_ids, g["gene"], species
                )
                verified.append({
                    "gene": g["gene"],
                    "species": g.get("species", ""),
                    "ncbi_found": len(gene_ids) > 0,
                    "gene_ids": gene_ids[:3],
                })
                await asyncio.sleep(0.34)

            yield {"type": "sop_ncbi_verified", "genes": verified}
            yield {"type": "done"}

        except Exception as e:
            logger.exception("[Agent] SOP 快捷路径异常")
            yield {"type": "error", "data": str(e)}
        finally:
            exp_pipeline.cleanup()

    # ------------------------------------------------------------------
    # 主运行循环（async generator）
    # ------------------------------------------------------------------
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
        """异步生成器，yield SSE 兼容事件 dict。

        事件类型：
          skill_selected, tool_call, tool_result, text, done, error
        """
        try:
            # ---- SOP 快捷路径：检测到 SOP 关键词，跳过工具调用循环 ----
            if _SOP_SHORTCUT_RE.search(user_input):
                logger.info("[Agent] SOP 快捷路径命中: %s", user_input[:80])
                async for event in self._run_sop_shortcut(
                    user_input=user_input,
                    history=history,
                    model_id=model_id,
                ):
                    yield event
                return

            # 1. 解析启用的工具
            enabled_tools = self._resolve_enabled_tools(
                user_id=user_id,
                use_depth=use_depth,
                use_personal=use_personal,
                skill_prefs=skill_prefs,
                tool_overrides=tool_overrides,
            )

            # 发送当前启用的工具和技能信息
            yield {
                "type": "tools_enabled",
                "tools": sorted(enabled_tools),
            }

            # 2. 构建消息列表
            system_prompt = self._build_system_prompt(
                user_id=user_id,
                use_depth=use_depth,
                use_personal=use_personal,
                enabled_tools=enabled_tools,
            )
            messages = [{"role": "system", "content": system_prompt}]

            # 注入截断的历史（新一轮对话，清理旧 reasoning_content 以节省 token）
            if history:
                truncated = self._truncate_history(history)
                if self._is_reasoner_model(model_id):
                    truncated = self._strip_reasoning_for_new_turn(truncated)
                messages.extend(truncated)

            messages.append({"role": "user", "content": user_input})

            # 3. 获取过滤后的工具定义
            tool_definitions = self._filter_tool_definitions(enabled_tools)

            # 4. 工具调用循环
            step = 0
            collected_tool_results = []  # 收集工具结果用于提取来源
            answer_text = ""  # 累积回答文本用于基因检测
            while step < MAX_STEPS:
                step += 1

                # ---- 上下文管理: 每次 LLM 调用前检查并压缩 ----
                messages = await self.context_mgr.prepare(messages, tool_definitions)

                try:
                    msg = await self.call_llm(
                        messages,
                        tools=tool_definitions if tool_definitions else None,
                        model_id=model_id,
                        temperature=0.3,
                    )
                except Exception as exc:
                    # L3: 检测 context overflow，紧急截断后重试
                    if self.context_mgr.is_overflow_error(exc):
                        logger.warning("检测到 context overflow，执行 L3 紧急截断")
                        messages = self.context_mgr.emergency_truncate(messages)
                        try:
                            msg = await self.call_llm(
                                messages,
                                tools=tool_definitions if tool_definitions else None,
                                model_id=model_id,
                                temperature=0.3,
                            )
                        except Exception as retry_exc:
                            logger.exception("L3 重试仍然失败")
                            yield {"type": "error", "data": str(retry_exc)}
                            return
                    else:
                        raise

                # ---- 记录 API 返回的 usage（如果有） ----
                if hasattr(msg, '_raw_response'):
                    try:
                        usage = msg._raw_response.get("usage", {})
                        if usage:
                            self.context_mgr.update_usage(usage, len(messages))
                    except Exception:
                        pass

                # ---- 将 assistant message 转为 dict 追加 ----
                # DeepSeek reasoner: 需要保留 reasoning_content 供同一轮工具调用循环使用
                messages.append(self._msg_to_dict(msg, model_id))

                # 没有工具调用 → 流式生成最终回答
                if not msg.tool_calls:
                    # 移除非流式拿到的完整回答，用流式重新生成实现逐字输出
                    messages.pop()

                    # 收集前几个 chunk 检测是否为泄露的 function call JSON
                    buffer = ""
                    buffer_chunks = []
                    flushed = False

                    async for chunk in self.call_llm_stream(
                        messages, model_id=model_id, temperature=0.3,
                    ):
                        if not chunk.choices:
                            continue
                        delta = chunk.choices[0].delta
                        # 跳过 reasoning_content（DeepSeek 思考过程，不应展示给用户）
                        if not delta.content:
                            continue
                        text_piece = delta.content

                        if not flushed:
                            # 缓冲前 200 字符，检测是否为泄露的 function call
                            buffer += text_piece
                            buffer_chunks.append(text_piece)
                            if len(buffer) < 200:
                                continue
                            # 检查缓冲区是否包含 function call JSON 泄露
                            if _FUNC_CALL_LEAK_RE.search(buffer):
                                logger.warning(
                                    "检测到流式输出中泄露了 function call JSON，"
                                    "丢弃并重新生成纯文本回答"
                                )
                                # 追加提示让模型用自然语言回答
                                messages.append({
                                    "role": "user",
                                    "content": (
                                        "请直接用自然语言回答上述问题，"
                                        "不要输出 JSON 或 function call 格式。"
                                    ),
                                })
                                buffer = ""
                                buffer_chunks = []
                                # 重新流式请求
                                async for retry_chunk in self.call_llm_stream(
                                    messages, model_id=model_id, temperature=0.3,
                                ):
                                    if retry_chunk.choices and retry_chunk.choices[0].delta.content:
                                        t = retry_chunk.choices[0].delta.content
                                        answer_text += t
                                        yield {"type": "text", "data": t}
                                flushed = True
                                break
                            else:
                                # 缓冲区正常，一次性 flush
                                for buffered_piece in buffer_chunks:
                                    answer_text += buffered_piece
                                    yield {"type": "text", "data": buffered_piece}
                                flushed = True
                        else:
                            answer_text += text_piece
                            yield {"type": "text", "data": text_piece}

                    # flush 剩余缓冲（内容少于 200 字符的短回答）
                    if not flushed and buffer_chunks:
                        if not _FUNC_CALL_LEAK_RE.search(buffer):
                            for buffered_piece in buffer_chunks:
                                answer_text += buffered_piece
                                yield {"type": "text", "data": buffered_piece}
                        else:
                            logger.warning("短回答中检测到 function call 泄露，已过滤")
                            yield {
                                "type": "text",
                                "data": "抱歉，模型返回了异常格式，请重新提问。",
                            }

                    # 发送参考文献来源（只保留正文中实际引用的文献）
                    all_sources = self._extract_sources_from_tool_results(collected_tool_results)
                    sources = self._filter_cited_sources(answer_text, all_sources)
                    if sources:
                        yield {"type": "sources", "data": sources}

                    # 检测基因名 → 触发前端基因编辑器 + SOP 按钮
                    if answer_text:
                        detected_genes = extract_gene_names(answer_text)
                        if detected_genes:
                            yield {"type": "genes_available", "genes": detected_genes}

                    yield {"type": "done"}
                    return

                # 处理工具调用
                for tc in msg.tool_calls:
                    tool_name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        args = {}

                    # 检测 skill 选择（agent 读取 skill 文件）
                    if tool_name == "read_tool" and "skill.md" in args.get("file_path", ""):
                        try:
                            skill_name = Path(args["file_path"]).parent.name
                            yield {"type": "skill_selected", "data": skill_name}
                        except Exception:
                            pass

                    # 发送 tool_call 事件
                    yield {
                        "type": "tool_call",
                        "tool": tool_name,
                        "args": args,
                    }

                    # 执行工具（注入 user_id 供需要的工具使用）
                    try:
                        result = await self.registry.execute(tool_name, user_id=user_id, **args)
                        result_str = str(result) if result is not None else ""
                    except Exception as e:
                        logger.warning("工具 %s 执行失败: %s", tool_name, e)
                        result_str = f"工具执行失败: {e}"

                    # 截断过长的工具输出（防止单次结果撑爆上下文）
                    result_str = ContextManager.cap_tool_output(result_str)

                    # 发送 tool_result 事件（摘要）
                    summary = result_str[:200] + "..." if len(result_str) > 200 else result_str
                    yield {
                        "type": "tool_result",
                        "tool": tool_name,
                        "summary": summary,
                    }

                    # 收集工具结果用于提取来源
                    collected_tool_results.append({
                        "tool": tool_name,
                        "content": result_str,
                    })

                    # 将结果注入消息
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result_str,
                    })

            # 达到最大步数
            yield {"type": "text", "data": "达到最大工具调用轮数，任务可能未完成。"}
            yield {"type": "done"}

        except Exception as e:
            logger.exception("Agent 运行异常")
            yield {"type": "error", "data": str(e)}
