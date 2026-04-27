from __future__ import annotations

import asyncio
from typing import Any


class RetrievalService:
    """Tool-neutral retrieval boundary around the current gene retriever."""

    def __init__(self, *, retriever: Any):
        self.retriever = retriever

    @property
    def total_chunks(self) -> int:
        return len(getattr(self.retriever, "chunks", []))

    def build_index(self, *, force: bool = False, incremental: bool = True) -> None:
        self.retriever.build_index(force=force, incremental=incremental)

    def search_gene_chunks(
        self,
        query: str,
        *,
        top_k: int = 20,
        use_hybrid: bool = True,
        rerank: bool = True,
        rerank_top_n: int = 50,
    ):
        return asyncio.run(
            self.asearch_gene_chunks(
                query,
                top_k=top_k,
                use_hybrid=use_hybrid,
                rerank=rerank,
                rerank_top_n=rerank_top_n,
            )
        )

    async def asearch_gene_chunks(
        self,
        query: str,
        *,
        top_k: int = 20,
        use_hybrid: bool = True,
        rerank: bool = True,
        rerank_top_n: int = 50,
    ):
        if use_hybrid and hasattr(self.retriever, "hybrid_search"):
            return await self.retriever.hybrid_search(
                query,
                top_k=top_k,
                rerank=rerank,
                rerank_top_n=rerank_top_n,
            )
        return await asyncio.to_thread(self.retriever.search, query, top_k)
