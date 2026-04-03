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
5. **不要显示基因名**: 在引用来源清单中不要列出基因名称

## 输出格式
1. 先给出核心答案
2. 然后分点详细说明，每个关键信息标注来源编号 [1] [2] 等
3. 如果回答涉及具体基因且有实验验证或改良的需求，在最后加一个"**最终建议**"小节，给出可操作的建议（如推荐靶点基因、实验方向等）
4. 最后列出"引用来源清单"，格式为：
   - [编号] 文章标题 - 链接
   例如：
   - [1] Biosynthesis and regulation of anthocyanin pathway genes - https://pubmed.ncbi.nlm.nih.gov/12345678/
   - [2] Genetic control of carotenoid biosynthesis in rice - https://pubmed.ncbi.nlm.nih.gov/23456789/
"""

DEEP_SYSTEM_PROMPT = """你是一个资深的植物分子生物学专家，正在进行**深度调研**。请基于检索到的大量多来源信息，撰写一份全面、系统的综合分析报告。
信息来源可能包括：基因数据库、PubMed 文献、用户个人知识库。

## 报告要求
1. **全面性**: 综合所有检索结果，覆盖尽可能多的基因和通路信息
2. **系统性**: 按逻辑分类组织（如按基因功能、代谢通路、物种等），形成完整知识框架
3. **深度分析**: 不仅罗列信息，还要分析基因间的调控关系、通路交叉、功能协同
4. **来源标注**: 在正文中用数字编号标注来源 [1] [2] 等
5. **专业性**: 使用准确的专业术语，适合科研人员阅读
6. **不要显示基因名**: 在引用来源清单中不要列出基因名称

## 报告结构
1. **概述**: 对问题的整体回答（2-3段）
2. **核心基因分析**: 逐个分析关键基因的功能、机制、实验证据
3. **代谢通路与调控网络**: 基因间的关系、上下游调控
4. **物种比较**（如适用）: 不同物种中的保守性与差异
5. **最终建议**: 基于以上分析，给出明确、可操作的实践建议（如育种策略、基因编辑靶点优先级、实验验证路线等）。如果涉及具体基因的功能验证或改良，建议列出推荐的靶点基因及实验方向
6. **引用来源清单**: 列出所有引用的来源，格式: [编号] 文章标题 - 链接

## 重要：不要在报告中加入"检索结果不足"或"当前检索局限性"之类的声明或免责段落。只基于已有信息给出分析和建议即可。
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

    def _build_messages(self, query: str, results, use_depth: bool = False) -> tuple[list[dict], int]:
        """构造发送给 LLM 的消息列表。"""
        context = format_context(results)
        source_list = format_source_list(results)

        if use_depth:
            n = len(results) if not isinstance(results, tuple) else len(results)
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
            messages = [
                {"role": "system", "content": DEEP_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
            return messages, 8192

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
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
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

    def generate_stream_with_tools(self, query: str, results, use_depth: bool = False):
        """流式生成答案。始终先由 LLM 回答，SOP 按钮由前端根据 genes_available 信号决定。"""
        messages, max_tokens = self._build_messages(query, results, use_depth=use_depth)
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
