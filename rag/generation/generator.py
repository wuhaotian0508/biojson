"""
LLM 生成模块 — 基于多来源检索结果生成专业回答

职责：
  1. 将统一格式的检索结果格式化为 LLM 上下文
  2. 根据模式选择 system prompt（普通/深度/追问）
  3. 管理对话历史截断，防止 context 超限
  4. 支持流式和非流式两种生成方式

支持的来源类型（source_type）：
  - gene_db   : 基因数据库检索结果
  - pubmed    : PubMed 文献摘要
  - jina_web  : 网页搜索结果
  - personal  : 用户个人知识库
"""
from typing import List, Dict

import openai
from openai import OpenAI

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, FALLBACK_API_KEY, FALLBACK_BASE_URL, FALLBACK_MODEL

SYSTEM_PROMPT = """你是一个专业的植物分子生物学专家，基于检索到的多来源信息回答用户问题。
信息来源可能包括：基因数据库、PubMed 文献、用户个人知识库。

## 回答要求
1. **准确性**: 只使用检索结果中的信息，不要编造
2. **结构化**: 使用清晰的结构组织答案
3. **专业性**: 使用准确的专业术语
4. **文中来源标注**: 在正文中用数字编号标注来源 [1] [2] 等
5. **不要在末尾列参考文献**: 系统会自动在回答末尾附上参考文献列表，你不需要在回答最后添加"参考文献"或"参考来源"等章节

## 输出格式
请使用 Markdown 格式输出，充分利用以下元素使回答清晰易读：
- 使用 ## 和 ### 标题来组织章节
- 使用 **加粗** 突出关键基因名、蛋白名等重要术语
- 使用有序/无序列表来罗列要点
- 必要时使用表格来对比信息
- 使用 > 引用块来标注重要结论或关键发现

"""

DEEP_SYSTEM_PROMPT = """你是一个资深的植物分子生物学专家，正在进行**深度调研**。请基于检索到的大量多来源信息，撰写一份全面、系统的综合分析报告。
信息来源可能包括：基因数据库、PubMed 文献、用户个人知识库。

## 报告要求
1. **系统性**: 对于检索结果中的信息，按逻辑分类组织（如按基因功能、代谢通路、物种等），形成完整知识框架
2. **深度分析**: 不仅罗列信息，还要分析关键基因的功能、机制、实验证据，分析基因间的调控关系、通路交叉、功能协同
3. **科研专业性**: 使用准确的专业术语，更适合科研人员阅读
4. **文中来源标注**: 在正文中用数字编号标注来源 [1] [2] 等
5. **不要在末尾列参考文献**: 系统会自动在报告末尾附上参考文献列表，你不需要在回答最后添加"参考文献"或"参考来源"等章节

## 输出格式
请使用 Markdown 格式输出，充分利用以下元素使报告结构清晰：
- 使用 ## 和 ### 标题来划分章节（如：概述、关键基因分析、代谢通路、调控网络、总结与展望等）
- 使用 **加粗** 突出关键基因名、蛋白名、通路名等重要术语
- 使用有序/无序列表来罗列要点
- 使用表格来汇总和对比基因信息（如基因名、物种、功能、实验证据等）
- 使用 > 引用块来标注重要结论或关键发现

## 重要：不要在报告中加入"检索结果不足"或"当前检索局限性"之类的声明或免责段落。只基于已有信息给出分析和建议即可。
"""

# ---- 追问专用 prompt：不强制固定结构，直接回答 ----

FOLLOWUP_SYSTEM_PROMPT = """你是营养代谢领域的资深专家。你正在与用户进行多轮对话。

## 追问回答要求
1. **直接回答**: 针对用户的追问，不重复赘述之前的内容
2. **添加新来源**: 如果有新来源，最后简要列出本次回答新引用的来源

## 输出格式
请使用 Markdown 格式输出（标题、加粗、列表、表格等），保持与之前回答一致的风格。
"""

DEEP_FOLLOWUP_SYSTEM_PROMPT = """你是一个资深的植物分子生物学专家，正在与用户进行多轮深度调研对话。之前已经给过系统性的分析报告。

## 追问回答要求
1. **聚焦追问**: 只针对用户新提出的问题展开，不要重复之前报告中已有的概述、基因分析、通路描述等
2. **深入补充**: 如果追问涉及之前未覆盖的方面，做深入分析；如果是已覆盖内容的细化，直接给出更详细的信息
3. **来源标注**: 关键信息标注来源编号 [1] [2]
4. **专业性**: 使用准确的专业术语

## 输出格式
- 使用 Markdown 格式输出，根据追问内容选择合适的结构（标题、列表、表格、加粗等），不需要重复完整的报告框架
- 最后列出本次回答新引用的来源
"""


def format_context(results: List[Dict]) -> str:
    """格式化检索结果作为上下文（统一 dict 格式）"""
    context_parts = []

    for i, item in enumerate(results, 1):
        src = item.get("source_type", "unknown")
        if src == "gene_db":
            source = f"[{item.get('title', '')} | {item.get('metadata', {}).get('gene_name', '')}]"
            extra = f"期刊: {item.get('metadata', {}).get('journal', '')}\n基因类型: {item.get('metadata', {}).get('gene_type', '')}\n"
        elif src == "pubmed":
            pmid = item.get("metadata", {}).get("pmid", "")
            journal = item.get("metadata", {}).get("journal", "")
            source = f"[{item.get('title', '')} | PMID:{pmid}]"
            extra = f"期刊: {journal}\nPubMed URL: {item.get('url', '')}\n"
        elif src == "jina_web":
            source = f"[{item.get('title', '')} | Web]"
            extra = f"URL: {item.get('url', '')}\n"
        elif src == "personal":
            fname = item.get("metadata", {}).get("filename", "")
            page = item.get("metadata", {}).get("page", "")
            source = f"[{fname} | p.{page}]"
            extra = ""
        else:
            source = f"[{item.get('title', '')}]"
            extra = ""

        score = item.get("score", 0.0)
        content = item.get("content", "")

        context_parts.append(f"""
=== 来源 {i}: {source} (来源类型: {src}) ===
{extra}相关性分数: {score:.4f}

{content}
""")

    return "\n".join(context_parts)


def format_source_list(results: List[Dict]) -> str:
    """生成来源清单"""
    sources = []
    for item in results:
        src = item.get("source_type", "unknown")
        title = item.get("title", "")
        if src == "gene_db":
            gene = item.get("metadata", {}).get("gene_name", "")
            line = f"- [基因库] {gene}: {title}"
        elif src == "pubmed":
            pmid = item.get("metadata", {}).get("pmid", "")
            line = f"- [PubMed] {title} (PMID:{pmid})"
        elif src == "jina_web":
            url = item.get("url", "")
            line = f"- [网页] {title} ({url})"
        elif src == "personal":
            fname = item.get("metadata", {}).get("filename", "")
            page = item.get("metadata", {}).get("page", "")
            line = f"- [个人库] {fname} p.{page}"
        else:
            line = f"- {title}"
        sources.append(line)
    return "\n".join(sources)


class RAGGenerator:
    """
    RAG 回答生成器 — 基于检索上下文调用 LLM 生成回答。

    支持：
      - 普通模式：简洁回答 (max_tokens=4096)
      - 深度调研模式：系统性分析报告 (max_tokens=8192)
      - 追问模式：不重复之前内容，聚焦新问题
      - 流式输出：SSE 事件逐 chunk 返回
    """

    def __init__(self, client=None):
        """
        参数:
            client: OpenAI 客户端实例（可注入自定义实例，用于测试）
        """
        # ---- 主 LLM 客户端（优先使用主 API） ----
        self.client = client or OpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL
        )
        self.model = LLM_MODEL

        # ---- Fallback LLM 客户端（主 API 内容过滤报 400 时自动切换） ----
        # 仅在 .env 中配置了 FALLBACK_API_KEY 时才创建，否则为 None
        self.fallback_client = (
            OpenAI(api_key=FALLBACK_API_KEY, base_url=FALLBACK_BASE_URL)
            if FALLBACK_API_KEY else None
        )
        # fallback_model：fallback 使用的模型名；未配置时退回主模型名
        self.fallback_model = FALLBACK_MODEL or LLM_MODEL

    @staticmethod
    def _truncate_history(history: list, max_chars_per_msg: int = 800) -> list:
        """截断历史消息，避免 context 过长。
        每条 assistant 消息最多保留 max_chars_per_msg 字符，user 消息保留原文。
        """
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

    def _build_messages(self, query: str, results, use_depth: bool = False, history: list = None) -> tuple[list[dict], int]:
        """构造发送给 LLM 的消息列表。"""
        context = format_context(results)
        source_list = format_source_list(results)

        is_followup = bool(history and len(history) >= 2)
        truncated_history = self._truncate_history(history) if history else []

        if use_depth:
            n = len(results) if not isinstance(results, tuple) else len(results)

            if is_followup:
                # 追问：用轻量 prompt，不强制完整报告结构
                user_prompt = f"""## 用户追问
{query}

## 检索到的相关信息（共 {n} 条）
{context}

## 可用来源清单
{source_list}

请针对上述追问，结合检索结果和之前对话的上下文进行回答。不需要重复之前已回答的内容。
"""
                sys_prompt = DEEP_FOLLOWUP_SYSTEM_PROMPT
            else:
                user_prompt = f"""## 用户问题
{query}

## 检索到的相关信息（共 {n} 条）
{context}

## 可用来源清单
{source_list}

请基于以上检索结果撰写一份**深度调研报告**。要求：
1. 综合所有 {n} 条检索结果，不要遗漏重要信息
2. 按照系统提示中的报告结构组织内容
3. 每个关键信息都要标注来源
4. 分析基因间的关联和调控关系
5. 不要加入"检索结果不足"之类的免责声明
"""
                sys_prompt = DEEP_SYSTEM_PROMPT

            messages = [{"role": "system", "content": sys_prompt}]
            if truncated_history:
                messages.extend(truncated_history)
            messages.append({"role": "user", "content": user_prompt})
            return messages, 8192

        if is_followup:
            # 追问：用轻量 prompt，不强制固定结构
            user_prompt = f"""## 用户追问
{query}

## 检索到的相关信息
{context}

## 可用来源清单
{source_list}

请针对上述追问，结合检索结果和之前对话的上下文进行回答。不需要重复之前已回答的内容。
"""
            sys_prompt = FOLLOWUP_SYSTEM_PROMPT
        else:
            user_prompt = f"""## 用户问题
{query}

## 检索到的相关信息
{context}

## 可用来源清单
{source_list}

请基于以上检索结果回答用户问题。记住：
1. 只使用检索结果中的信息
2. 每个关键信息都要标注来源
3. 不要加入"检索结果不足"之类的免责声明
"""
            sys_prompt = SYSTEM_PROMPT

        messages = [{"role": "system", "content": sys_prompt}]
        if truncated_history:
            messages.extend(truncated_history)
        messages.append({"role": "user", "content": user_prompt})
        return messages, 4096

    def generate(self, query: str, results,
                 stream: bool = False) -> str:
        """基于检索结果生成答案"""
        messages, max_tokens = self._build_messages(query, results)

        if stream:
            return self._stream_generate(messages, max_tokens=max_tokens)
        else:
            # ---- 先尝试主 API，内容过滤报 400 时切换 fallback ----
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=max_tokens
                )
            except openai.BadRequestError:
                # BadRequestError (HTTP 400)：通常由主 API 的内容审查触发
                # 若 fallback 未配置则向上重新抛出，不静默吞掉错误
                if not self.fallback_client:
                    raise
                response = self.fallback_client.chat.completions.create(
                    model=self.fallback_model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=max_tokens
                )
            return response.choices[0].message.content

    def _stream_generate(self, messages: List[Dict], max_tokens: int = 4096) -> str:
        """流式生成（内部方法，由 generate(stream=True) 调用）"""
        # ---- 先尝试主 API 建立流式连接，失败则切换 fallback ----
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=max_tokens,
                stream=True
            )
        except openai.BadRequestError:
            # 内容过滤导致的 400：用 fallback 重建流（从头开始，不会截断）
            if not self.fallback_client:
                raise
            response = self.fallback_client.chat.completions.create(
                model=self.fallback_model,
                messages=messages,
                temperature=0.3,
                max_tokens=max_tokens,
                stream=True
            )

        full_response = ""   # full_response: 拼接所有 chunk 的完整回答文本
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content
        print()
        return full_response

    def generate_stream_with_tools(self, query: str, results, use_depth: bool = False, history: list = None):
        """流式生成答案。始终先由 LLM 回答，SOP 按钮由前端根据 genes_available 信号决定。"""
        messages, max_tokens = self._build_messages(query, results, use_depth=use_depth, history=history)

        # ---- 先尝试主 API 建立 SSE 流，内容过滤 400 时切换 fallback ----
        # 注意：openai.BadRequestError 在 .create() 调用时立即抛出（连接建立阶段），
        # 而非流迭代中途，因此这里的 try/except 可以可靠地拦截内容过滤错误
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=max_tokens,
                stream=True
            )
        except openai.BadRequestError:
            # 用 fallback 重新建立流，整条回答从头开始生成
            if not self.fallback_client:
                raise
            response = self.fallback_client.chat.completions.create(
                model=self.fallback_model,
                messages=messages,
                temperature=0.3,
                max_tokens=max_tokens,
                stream=True
            )

        # ---- 逐 chunk yield 给调用方（pipeline → SSE 事件流） ----
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield {"type": "text", "data": chunk.choices[0].delta.content}
