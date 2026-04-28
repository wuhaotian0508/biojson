from __future__ import annotations

import asyncio
import logging
from typing import Any

from nutrimaster.agent.tools import BaseTool
from nutrimaster.agent.tools.retrieval.formatters import RENDERERS

logger = logging.getLogger(__name__)

_SOURCE_LABELS = {
    "pubmed": "PubMed",
    "gene_db": "基因数据库",
    "personal_lib": "个人知识库",
}


class RAGSearchTool(BaseTool):
    name = "rag_search"
    description = "综合搜索 PubMed 文献、基因数据库和个人知识库，返回重排后的最相关结果"

    def __init__(self, sources: dict[str, Any], reranker):
        self._sources = dict(sources)
        self._reranker = reranker

    @property
    def schema(self) -> dict:
        source_keys = list(self._sources)
        default_sources = [key for key in ("pubmed", "gene_db") if key in self._sources] or source_keys
        description = f"要搜索的数据源列表。可选: {source_keys}。默认 {default_sources}"
        if "pubmed" in default_sources:
            description += "。注意：默认已包含 PubMed，无需再单独调用 pubmed_search 工具"
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": (
                    "综合搜索多个数据源（PubMed 文献、基因数据库、个人知识库），"
                    "自动进行跨来源语义重排，返回最相关的结果。"
                    "默认已包含 PubMed 搜索，无需再单独调用 pubmed_search 工具。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询（建议使用英文以获得最佳结果）",
                        },
                        "sources": {
                            "type": "array",
                            "items": {"type": "string", "enum": source_keys},
                            "description": description,
                        },
                        "top_n": {
                            "type": "integer",
                            "description": "返回重排后的结果数量，默认 10",
                        },
                        "user_id": {
                            "type": "string",
                            "description": "用户 ID（由系统自动注入，不要手动填写）",
                        },
                    },
                    "required": ["query"],
                },
            },
        }

    async def _safe_search(self, source_key: str, **kwargs) -> list[dict]:
        source = self._sources.get(source_key)
        if source is None:
            return []
        try:
            return await source.search_raw(**kwargs)
        except Exception as exc:
            logger.warning("%s search failed: %s", _SOURCE_LABELS.get(source_key, source_key), exc)
            return []

    async def execute(
        self,
        query: str,
        sources: list[str] | None = None,
        top_n: int = 10,
        user_id: str | None = None,
        **_,
    ) -> str:
        if sources is None:
            sources = [key for key in ("pubmed", "gene_db") if key in self._sources] or list(self._sources)

        tasks = []
        source_names = []
        for source_key in sources:
            if source_key not in self._sources:
                continue
            kwargs = {"query": query}
            if source_key == "personal_lib":
                kwargs["user_id"] = user_id
            tasks.append(self._safe_search(source_key, **kwargs))
            source_names.append(_SOURCE_LABELS.get(source_key, source_key))

        if not tasks:
            return "未指定有效的搜索数据源。"

        results_by_source = await asyncio.gather(*tasks)
        candidates = [item for source_results in results_by_source for item in source_results]
        if not candidates:
            return f"在 {', '.join(source_names)} 中未找到与 '{query}' 相关的结果。"

        if len(candidates) > top_n and self._reranker:
            try:
                ranked = await asyncio.to_thread(self._reranker.rerank, query, candidates, top_n)
            except Exception as exc:
                logger.warning("Rerank failed, using original order: %s", exc)
                ranked = candidates[:top_n]
        else:
            ranked = candidates[:top_n]
        return self._format_results(ranked, source_names)

    @staticmethod
    def _format_results(ranked: list[dict], source_names: list[str]) -> str:
        lines = [f"综合搜索结果（来源: {', '.join(source_names)}，共 {len(ranked)} 条）：\n"]
        references = []
        for index, item in enumerate(ranked, 1):
            source_type = item.get("source_type", "unknown")
            renderer = RENDERERS.get(source_type)
            if renderer:
                lines.extend(renderer(item, index, with_source_label=True))
                if source_type == "personal":
                    references.append(item.get("metadata", {}).get("filename", ""))
                else:
                    references.append(item.get("title", ""))
            else:
                title = item.get("title", "")
                lines.append(f"[{index}] {title}")
                lines.append(f"    来源: {source_type}")
                lines.append(f"    相关性: {item.get('score', 0.0):.4f}")
                lines.append(f"    内容: {item.get('content', '')}")
                references.append(title)
            lines.append("")
        if references:
            lines.append("=" * 60)
            lines.append("参考文献：")
            lines.append("")
            for index, reference in enumerate(references, 1):
                lines.append(f"[{index}] {reference}")
        return "\n".join(lines)
