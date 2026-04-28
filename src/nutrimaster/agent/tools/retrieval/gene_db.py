from __future__ import annotations

import asyncio
from typing import ClassVar

from nutrimaster.agent.tools import BaseTool
from nutrimaster.agent.tools.retrieval.formatters import render_gene_db


class GeneDBSearchTool(BaseTool):
    name = "gene_db_search"
    description = "检索本地基因数据库，基于向量相似度返回相关基因文献片段"
    source_type: ClassVar[str] = "gene_db"

    def __init__(self, retrieval_service=None, retriever=None):
        if retriever is None and retrieval_service is not None and not hasattr(retrieval_service, "search_gene_chunks"):
            retriever = retrieval_service
            retrieval_service = None
        self._retrieval_service = retrieval_service
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

    async def search_raw(
        self,
        query: str,
        top_k: int = 20,
        use_hybrid: bool = True,
        use_rerank: bool = True,
        **_,
    ) -> list[dict]:
        if self._retrieval_service is not None:
            chunks = self._retrieval_service.search_gene_chunks(
                query,
                top_k=top_k,
                use_hybrid=use_hybrid,
                rerank=use_rerank,
                rerank_top_n=50,
            )
        elif use_hybrid:
            chunks = await self._retriever.hybrid_search(
                query,
                top_k=top_k,
                rerank=use_rerank,
                rerank_top_n=50,
            )
        else:
            chunks = await asyncio.to_thread(self._retriever.search, query, top_k=top_k)

        return [
            {
                "source_type": self.source_type,
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
            }
            for chunk, score in chunks
        ]

    async def execute(self, query: str, top_k: int = 20, **_) -> str:
        items = await self.search_raw(query, top_k=top_k)
        if not items:
            return f"未找到与 '{query}' 相关的基因数据库记录。"
        lines = [f"基因数据库检索结果（共 {len(items)} 条）：\n"]
        for index, item in enumerate(items, 1):
            lines.extend(render_gene_db(item, index, with_source_label=False))
            lines.append("")
        return "\n".join(lines)
