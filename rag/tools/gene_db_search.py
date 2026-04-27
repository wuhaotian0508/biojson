"""
基因数据库检索工具 — 封装 search/retriever.py 的 JinaRetriever

功能：
  1. 向量检索：基于 Jina Embeddings v3 的语义相似度搜索
  2. 混合检索：BM25（关键词） + Dense（语义） RRF 融合
  3. 重排序：Cross-Encoder 精排（可选）
  4. 双接口：execute（格式化文本）+ search_raw（统一字典）

架构位置：
  - 独立调用：Agent 直接调用 gene_db_search 工具
  - 聚合调用：rag_search 内部调用 search_raw，与 PubMed/个人库并行检索

检索流程：
  用户查询 → [BM25 + Dense 并行] → RRF 融合 → Cross-Encoder 重排 → top_k 结果

数据来源：
  rag/data/*.json（extractor 输出的已验证基因数据）
  → utils/chunker 切块（按基因字段分类）
  → Jina Embeddings 向量化
  → 存储在 rag/index/（chunks.pkl + embeddings.npy + bm25.pkl）
"""
import asyncio
from typing import ClassVar

from tools.base import BaseTool


class GeneDBSearchTool(BaseTool):
    name = "gene_db_search"
    description = "检索本地基因数据库，基于向量相似度返回相关基因文献片段"
    source_type: ClassVar[str] = "gene_db"

    def __init__(self, retriever):
        self._retriever = retriever

    @property
    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "检索查询",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "返回结果数量，默认 20",
                        },
                    },
                    "required": ["query"],
                },
            },
        }

    async def search_raw(self, query: str, top_k: int = 20, use_hybrid: bool = True,
                         use_rerank: bool = True, **_) -> list[dict]:
        """
        调用 JinaRetriever 检索，转换为统一字典结构（供 rag_search 复用）。

        参数:
            query:       检索查询（中英文均可，自动分词）
            top_k:       返回结果数量（默认 20）
            use_hybrid:  是否使用 BM25+Dense 混合检索（默认 True）
                         - True: BM25 + Dense RRF 融合（推荐，兼顾关键词和语义）
                         - False: 纯 Dense 向量检索（向后兼容）
            use_rerank:  是否使用 Cross-Encoder 重排（默认 True，仅在 use_hybrid=True 时生效）
                         - True: 从 RRF top-50 中用 Jina Reranker 精排出 top_k
                         - False: 直接返回 RRF top_k

        返回:
            统一字典列表，每个元素包含：
              - source_type: "gene_db"（来源标识）
              - title: 论文标题
              - content: chunk 文本内容（用于 Reranker 计算相关性）
              - url: DOI 链接（https://doi.org/...）
              - score: 相关性分数（RRF 或 Reranker 输出）
              - metadata: {gene_name, gene_type, journal, doi}

        工作流程：
            1. 如果 use_hybrid=True:
                 a. BM25 检索 top-50（关键词匹配，捕捉专有名词）
                 b. Dense 检索 top-50（语义相似度）
                 c. RRF 融合（Reciprocal Rank Fusion）
                 d. 如果 use_rerank=True: Jina Reranker 精排 → top_k
                    否则: 直接截断 top_k
            2. 如果 use_hybrid=False:
                 纯 Dense 检索 top_k（向后兼容旧版本）
        """
        if use_hybrid:
            # 使用 BM25+Dense RRF 混合检索 + 可选 rerank
            chunks = await self._retriever.hybrid_search(
                query,
                top_k=top_k,
                rerank=use_rerank,
                rerank_top_n=50,  # 从 RRF top-50 中 rerank 出 top_k
            )
        else:
            # 纯稠密向量检索（向后兼容）
            chunks = await asyncio.to_thread(self._retriever.search, query, top_k=top_k)

        results = []
        for chunk, score in chunks:
            results.append({
                "source_type": "gene_db",
                "title": chunk.paper_title,
                "content": chunk.content,
                "url": f"https://doi.org/{chunk.doi}" if chunk.doi else "",
                "score": score,
                "metadata": {
                    "gene_name": chunk.gene_name,
                    "gene_type": chunk.gene_type,
                    "journal": chunk.journal,
                    "doi": chunk.doi,
                },
            })
        return results

    async def execute(self, query: str, top_k: int = 20, **_) -> str:
        """
        Agent 直接调用的入口 — 返回格式化的可读文本。

        与 search_raw 的区别：
          - search_raw: 返回 list[dict]，供 rag_search 聚合使用
          - execute: 返回格式化的字符串，直接注入 Agent 消息

        参数:
            query: 检索查询
            top_k: 返回结果数量

        返回:
            格式化的检索结果文本，包含：
              - 标题、基因名、类型、期刊、DOI、相关性分数、内容摘要
              - 每条结果用编号 [1], [2], ... 标识（供 Agent 引用）
        """
        from tools._formatters import render_gene_db

        items = await self.search_raw(query, top_k=top_k)
        if not items:
            return f"未找到与 '{query}' 相关的基因数据库记录。"

        lines = [f"基因数据库检索结果（共 {len(items)} 条）：\n"]
        for i, item in enumerate(items, 1):
            lines.extend(render_gene_db(item, i, with_source_label=False))
            lines.append("")
        return "\n".join(lines)
