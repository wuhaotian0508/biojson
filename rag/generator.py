"""基于检索结果的LLM生成模块 - 支持多来源（基因库 / PubMed / 网页 / 个人库）"""
from typing import List, Dict

from openai import OpenAI

from data_loader import GeneChunk
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

SYSTEM_PROMPT = """你是一个专业的植物分子生物学专家，基于检索到的多来源信息回答用户问题。
信息来源可能包括：基因数据库、PubMed 文献、用户个人知识库。

## 回答要求
1. **准确性**: 只使用检索结果中的信息，不要编造
2. **来源标注**: 在正文中用数字编号标注来源，如 [1]、[2]
3. **结构化**: 使用清晰的结构组织答案
4. **专业性**: 使用准确的专业术语

"""

DEEP_SYSTEM_PROMPT = """你是一个资深的植物分子生物学专家，正在进行**深度调研**。请基于检索到的大量多来源信息，撰写一份全面、系统的综合分析报告。
信息来源可能包括：基因数据库、PubMed 文献、用户个人知识库。

## 报告要求
1. **全面性**: 综合所有检索结果，覆盖尽可能多的基因和通路信息
2. **系统性**: 按逻辑分类组织（如按基因功能、代谢通路、物种等），形成完整知识框架
3. **深度分析**: 不仅罗列信息，还要分析基因间的调控关系、通路交叉、功能协同
4. **来源标注**: 在正文中用数字编号标注来源 [1] [2] 等
5. **专业性**: 使用准确的专业术语，适合科研人员阅读



## 重要：不要在报告中加入"检索结果不足"或"当前检索局限性"之类的声明或免责段落。只基于已有信息给出分析和建议即可。
"""

# ---- 追问专用 prompt：不强制固定结构，直接回答 ----

FOLLOWUP_SYSTEM_PROMPT = """你是一个专业的植物分子生物学专家。你正在与用户进行多轮对话，之前已经给过详细回答。

## 追问回答要求
1. **直接回答**: 针对用户的追问直奔主题，不要重复概述、分析框架、物种比较等之前已涵盖的内容
2. **准确性**: 只使用检索结果中的信息，不要编造
3. **来源标注**: 关键信息标注来源编号 [1] [2]
4. **简洁**: 回答长度与问题复杂度匹配。简单追问用几段话即可，不需要写完整报告
5. **不要显示基因名**: 在引用来源清单中不要列出基因名称

## 输出格式
- 自由组织，不要套用固定模板（不需要"概述→分析→比较→建议"的完整结构）
- 如果追问涉及新的具体建议，可以加"**建议**"小节
- 最后简要列出本次回答新引用的来源（如果有新来源）
"""

DEEP_FOLLOWUP_SYSTEM_PROMPT = """你是一个资深的植物分子生物学专家，正在与用户进行多轮深度调研对话。之前已经给过系统性的分析报告。

## 追问回答要求
1. **聚焦追问**: 只针对用户新提出的问题展开，不要重复之前报告中已有的概述、基因分析、通路描述等
2. **深入补充**: 如果追问涉及之前未覆盖的方面，做深入分析；如果是已覆盖内容的细化，直接给出更详细的信息
3. **来源标注**: 关键信息标注来源编号 [1] [2]
4. **专业性**: 使用准确的专业术语

## 输出格式
- 自由组织，根据追问内容选择合适的结构，不需要重复完整的报告框架
- 最后列出本次回答新引用的来源
"""


def format_context(results) -> str:
    """格式化检索结果作为上下文

    接受两种格式:
      - List[Dict]: 统一结果字典 (新格式，多来源)
      - List[Tuple[GeneChunk, float]]: 旧格式 (基因库)
    """
    context_parts = []

    for i, item in enumerate(results, 1):
        # 统一字典格式
        if isinstance(item, dict):
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
        # 兼容旧格式: (GeneChunk, float)
        elif isinstance(item, tuple) and len(item) == 2:
            chunk, score = item
            source = f"[{chunk.paper_title} | {chunk.gene_name}]"
            context_parts.append(f"""
=== 来源 {i}: {source} ===
期刊: {chunk.journal}
基因类型: {chunk.gene_type}
相关性分数: {score:.4f}

{chunk.content}
""")

    return "\n".join(context_parts)


def format_source_list(results) -> str:
    """生成来源清单（兼容两种格式）"""
    sources = []
    for item in results:
        if isinstance(item, dict):
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
        elif isinstance(item, tuple) and len(item) == 2:
            chunk, score = item
            line = f"- {chunk.gene_name}: {chunk.paper_title}"
            if chunk.doi:
                line += f" DOI: {chunk.doi}"
            sources.append(line)
    return "\n".join(sources)


class RAGGenerator:
    """RAG生成器"""

    def __init__(self, client=None):
        self.client = client or OpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL
        )
        self.model = LLM_MODEL

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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content

    def _stream_generate(self, messages: List[Dict], max_tokens: int = 4096) -> str:
        """流式生成"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=max_tokens,
            stream=True
        )

        full_response = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content
        print()
        return full_response

    def generate_stream(self, query: str, results):
        """流式生成答案，逐 token yield（用于 Web 界面）"""
        messages, max_tokens = self._build_messages(query, results)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=max_tokens,
            stream=True
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def generate_deep_stream(self, query: str, results):
        """深度调研流式生成，使用更详细的提示词和更大的 max_tokens"""
        messages, max_tokens = self._build_messages(query, results, use_depth=True)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=max_tokens,
            stream=True
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def generate_stream_with_tools(self, query: str, results, use_depth: bool = False, history: list = None):
        """流式生成答案。始终先由 LLM 回答，SOP 按钮由前端根据 genes_available 信号决定。"""
        messages, max_tokens = self._build_messages(query, results, use_depth=use_depth, history=history)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=max_tokens,
            stream=True
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield {"type": "text", "data": chunk.choices[0].delta.content}


if __name__ == "__main__":
    from retriever import JinaRetriever

    # 加载索引
    retriever = JinaRetriever()
    retriever.build_index()

    # 测试
    query = "植物中DREB转录因子如何调控抗旱性？"
    results = retriever.retrieve(query)

    generator = RAGGenerator()
    answer = generator.generate(query, results, stream=True)
