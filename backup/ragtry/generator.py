"""基于检索结果的LLM生成模块 - 带来源标注"""
from typing import List, Tuple, Dict, Any
from openai import OpenAI

from backup.ragtry.data_loader import GeneChunk
from backup.ragtry.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

SYSTEM_PROMPT = """你是一个专业的植物分子生物学专家，基于检索到的基因数据库信息回答用户问题。

## 回答要求
1. **准确性**: 只使用检索结果中的信息，不要编造
2. **来源标注**: 每个关键信息必须标注来源，格式为 [文章名 | 基因名]
3. **结构化**: 使用清晰的结构组织答案
4. **专业性**: 使用准确的专业术语

## 来源标注示例
- "DREB1A通过结合DRE元件激活下游抗旱基因 [AnDHN, a Dehydrin Protein From... | DREB1A]"
- "MYB转录因子家族在干旱响应中起关键作用 [Title of Paper | MYB51]"

## 输出格式
1. 先给出核心答案
2. 然后分点详细说明，每点都要有来源标注
3. 最后列出所有引用的来源清单
"""

def format_context(results: List[Tuple[GeneChunk, float]]) -> str:
    """格式化检索结果作为上下文"""
    context_parts = []

    for i, (chunk, score) in enumerate(results, 1):
        source = f"[{chunk.article_title} | {chunk.gene_name}]"
        context_parts.append(f"""
=== 来源 {i}: {source} ===
物种: {chunk.species}
类别: {chunk.category}
相关性分数: {score:.4f}

{chunk.text}
""")

    return "\n".join(context_parts)

def format_source_list(results: List[Tuple[GeneChunk, float]]) -> str:
    """生成来源清单"""
    sources = []
    for chunk, score in results:
        sources.append(f"- {chunk.gene_name} ({chunk.species}): {chunk.article_title}")
        if chunk.doi:
            sources[-1] += f" DOI: {chunk.doi}"
    return "\n".join(sources)

class RAGGenerator:
    """RAG生成器"""

    def __init__(self):
        self.client = OpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL
        )
        self.model = LLM_MODEL

    def generate(self, query: str, results: List[Tuple[GeneChunk, float]],
                 stream: bool = False) -> str:
        """基于检索结果生成答案"""

        context = format_context(results)
        source_list = format_source_list(results)

        user_prompt = f"""## 用户问题
{query}

## 检索到的相关基因信息
{context}

## 可用来源清单
{source_list}

请基于以上检索结果回答用户问题。记住：
1. 只使用检索结果中的信息
2. 每个关键信息都要标注来源 [文章名 | 基因名]
3. 如果检索结果不足以回答问题，明确说明
"""

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        if stream:
            return self._stream_generate(messages)
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=4096
            )
            return response.choices[0].message.content

    def _stream_generate(self, messages: List[Dict]) -> str:
        """流式生成"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=4096,
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

    def generate_stream(self, query: str, results: List[Tuple[GeneChunk, float]]):
        """流式生成答案，逐 token yield（用于 Web 界面）"""
        context = format_context(results)
        source_list = format_source_list(results)

        user_prompt = f"""## 用户问题
{query}

## 检索到的相关基因信息
{context}

## 可用来源清单
{source_list}

请基于以上检索结果回答用户问题。记住：
1. 只使用检索结果中的信息
2. 每个关键信息都要标注来源 [文章名 | 基因名]
3. 如果检索结果不足以回答问题，明确说明
"""

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=4096,
            stream=True
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


if __name__ == "__main__":
    from backup.ragtry.retriever import JinaRetriever

    # 加载索引
    retriever = JinaRetriever()
    retriever.build_index()

    # 测试
    query = "植物中DREB转录因子如何调控抗旱性？"
    results = retriever.retrieve(query)

    generator = RAGGenerator()
    answer = generator.generate(query, results, stream=True)
