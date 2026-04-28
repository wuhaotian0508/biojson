from __future__ import annotations

import asyncio
import json
import logging
import re
import xml.etree.ElementTree as ET
from collections.abc import Awaitable
from dataclasses import dataclass
from typing import Any, Callable

import httpx

from nutrimaster.rag.evidence import EvidenceFusion, EvidenceItem, EvidencePacket, SourceCollector

logger = logging.getLogger(__name__)
PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


@dataclass(frozen=True)
class RAGSearchContext:
    user_id: str | None = None
    include_personal: bool = False
    mode: str = "normal"
    focus: str = "general"
    top_k: int = 10


class RAGSearchService:
    """Composite evidence search used by the agent-facing rag_search tool."""

    def __init__(
        self,
        *,
        pubmed_source: Any,
        gene_db_source: Any,
        personal_source: Any | None = None,
        fusion: EvidenceFusion | None = None,
        source_collector: SourceCollector | None = None,
    ):
        self.pubmed_source = pubmed_source
        self.gene_db_source = gene_db_source
        self.personal_source = personal_source
        self.fusion = fusion or EvidenceFusion()
        self.source_collector = source_collector or SourceCollector()

    async def search(self, query: str, context: RAGSearchContext | None = None) -> EvidencePacket:
        context = context or RAGSearchContext()
        source_budget = self._source_budget(context)
        tasks = {
            "pubmed": self._safe_search(self.pubmed_source, query, top_k=source_budget["pubmed"], context=context),
            "gene_db": self._safe_search(self.gene_db_source, query, top_k=source_budget["gene_db"], context=context),
        }
        if context.include_personal and self.personal_source is not None:
            tasks["personal"] = self._safe_search(
                self.personal_source,
                query,
                top_k=source_budget["personal"],
                context=context,
            )

        keys = list(tasks)
        results = await asyncio.gather(*tasks.values())
        results_by_source = dict(zip(keys, results))
        source_counts = {key: len(items) for key, items in results_by_source.items()}
        warnings = [
            f"{key} 未返回结果"
            for key, count in source_counts.items()
            if key in {"pubmed", "gene_db"} and count == 0
        ]

        fused = self.fusion.fuse(results_by_source, top_k=context.top_k)
        numbered = self.source_collector.assign(fused)
        return EvidencePacket(
            query=query,
            mode=context.mode,
            items=numbered,
            source_counts=source_counts,
            warnings=warnings,
        )

    @staticmethod
    def _source_budget(context: RAGSearchContext) -> dict[str, int]:
        if context.mode == "deep":
            return {"pubmed": 12, "gene_db": 20, "personal": 12}
        return {"pubmed": 6, "gene_db": 12, "personal": 8}

    @staticmethod
    async def _safe_search(source: Any, query: str, *, top_k: int, context: RAGSearchContext) -> list[EvidenceItem]:
        try:
            return await source.search(
                query,
                top_k=top_k,
                user_id=context.user_id,
                mode=context.mode,
                focus=context.focus,
            )
        except Exception as exc:
            logger.warning("%s search failed: %s", source.__class__.__name__, exc)
            return []


class PubMedQueryOptimizer:
    def __init__(self, *, api_key: str = "", base_url: str = "", model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def __call__(self, user_query: str) -> str:
        if not self.api_key or not self.base_url:
            return user_query
        if len(user_query.split()) <= 8 and any(op in user_query.upper() for op in ["AND", "OR", "NOT"]):
            return user_query
        prompt = f"""将以下生物学查询转换为 PubMed 搜索关键词。

用户查询: {user_query}

要求:
1. 提取 2-5 个核心关键词（基因名、化合物名、物种名、生物学过程）
2. 使用英文
3. 用 AND 连接必需词，OR 连接同义词
4. 总词数不超过 10 个
5. 只返回关键词组合，不要解释"""
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 200,
                    },
                )
                response.raise_for_status()
                optimized = response.json()["choices"][0]["message"]["content"].strip()
                return re.sub(r"^```.*?\n|```$", "", optimized, flags=re.MULTILINE).strip()
        except Exception as exc:
            logger.warning("PubMed query optimization failed: %s", exc)
            return user_query


class PubMedSource:
    source_type = "pubmed"

    def __init__(self, *, http_client_factory=None, query_optimizer=None):
        self._http_client_factory = http_client_factory or (lambda: httpx.AsyncClient(timeout=20))
        self._query_optimizer = query_optimizer or (lambda query: query)

    async def search(self, query: str, *, top_k: int = 8, **_: Any) -> list[EvidenceItem]:
        articles = await self._search_raw(query, max_results=top_k)
        return [
            EvidenceItem(
                source_id="",
                source_type=self.source_type,
                title=article["title"],
                content=article["abstract"],
                url=article["url"],
                pmid=article["pmid"],
                journal=article["journal"],
                score=0.0,
                metadata={"pmid": article["pmid"], "journal": article["journal"]},
            )
            for article in articles
        ]

    async def _optimize(self, query: str) -> str:
        result = self._query_optimizer(query)
        if hasattr(result, "__await__"):
            return await result
        return result

    async def _search_raw(self, query: str, max_results: int) -> list[dict[str, Any]]:
        search_query = await self._optimize(query)
        client = self._http_client_factory()
        close = getattr(client, "aclose", None)
        try:
            response = await client.get(
                PUBMED_ESEARCH_URL,
                params={
                    "db": "pubmed",
                    "term": search_query,
                    "retmax": max_results,
                    "retmode": "json",
                    "sort": "relevance",
                },
            )
            response.raise_for_status()
            ids = response.json().get("esearchresult", {}).get("idlist", [])
            if not ids:
                return []
            response = await client.get(
                PUBMED_EFETCH_URL,
                params={
                    "db": "pubmed",
                    "id": ",".join(ids),
                    "retmode": "xml",
                    "rettype": "abstract",
                },
            )
            response.raise_for_status()
            return self._parse_pubmed_xml(response.text)
        finally:
            if close is not None:
                await close()

    @staticmethod
    def _parse_pubmed_xml(xml_text: str) -> list[dict[str, str]]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []
        results = []
        for article in root.iter("PubmedArticle"):
            try:
                medline = article.find("MedlineCitation")
                article_element = medline.find("Article") if medline is not None else None
                if medline is None or article_element is None:
                    continue
                pmid_element = medline.find("PMID")
                title_element = article_element.find("ArticleTitle")
                abstract_parts = []
                abstract_element = article_element.find("Abstract")
                if abstract_element is not None:
                    for text_element in abstract_element.findall("AbstractText"):
                        label = text_element.get("Label", "")
                        text = "".join(text_element.itertext()).strip()
                        abstract_parts.append(f"{label}: {text}" if label else text)
                journal_element = article_element.find("Journal/Title")
                pmid = pmid_element.text if pmid_element is not None else ""
                results.append(
                    {
                        "pmid": pmid,
                        "title": "".join(title_element.itertext()).strip() if title_element is not None else "",
                        "abstract": "\n".join(abstract_parts) or "(no abstract)",
                        "journal": journal_element.text if journal_element is not None else "",
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    }
                )
            except Exception:
                continue
        return results


class GeneDbSource:
    source_type = "gene_db"

    def __init__(self, retriever: Any):
        self.retriever = retriever

    async def search(self, query: str, *, top_k: int = 12, **_: Any) -> list[EvidenceItem]:
        import inspect

        if hasattr(self.retriever, "hybrid_search"):
            maybe_results = self.retriever.hybrid_search(
                query,
                top_k=top_k,
                rerank=True,
                rerank_top_n=max(top_k * 4, 50),
            )
            results = await maybe_results if inspect.isawaitable(maybe_results) else maybe_results
        else:
            results = await asyncio.to_thread(self.retriever.search, query, top_k=top_k)
        return [
            EvidenceItem(
                source_id="",
                source_type=self.source_type,
                title=getattr(chunk, "paper_title", "") or "",
                content=getattr(chunk, "content", "") or "",
                doi=getattr(chunk, "doi", "") or "",
                journal=getattr(chunk, "journal", "") or "",
                gene_name=getattr(chunk, "gene_name", "") or "",
                score=float(score),
                metadata={
                    "gene_type": getattr(chunk, "gene_type", "") or "",
                    "chunk_type": getattr(chunk, "chunk_type", "") or "",
                },
            )
            for chunk, score in results
        ]


class PersonalLibrarySource:
    source_type = "personal"

    def __init__(
        self,
        *,
        get_personal_lib: Callable[[str], Any] | None = None,
        get_query_embedding: Callable[[str], Any] | None = None,
    ):
        self.get_personal_lib = get_personal_lib
        self.get_query_embedding = get_query_embedding

    async def search(
        self,
        query: str,
        *,
        top_k: int = 8,
        user_id: str | None = None,
        **_: Any,
    ) -> list[EvidenceItem]:
        if not user_id or self.get_personal_lib is None or self.get_query_embedding is None:
            return []
        library = self.get_personal_lib(user_id)
        query_embedding = await asyncio.to_thread(self.get_query_embedding, query)
        results = await asyncio.to_thread(library.search, query_embedding, top_k=top_k)
        output: list[EvidenceItem] = []
        for item in results:
            metadata = item.get("metadata", {})
            filename = metadata.get("filename", item.get("title", ""))
            page = metadata.get("page", "")
            output.append(
                EvidenceItem(
                    source_id="",
                    source_type=self.source_type,
                    title=f"{filename} (p.{page})" if page else filename,
                    content=item.get("content", ""),
                    score=float(item.get("score", 0.0)),
                    metadata=metadata,
                )
            )
        return output


class QueryTranslator:
    def __init__(self, call_llm: Callable[[str], Awaitable[str]] | None):
        self._call_llm = call_llm

    @classmethod
    def from_openai_compatible(
        cls,
        *,
        api_key: str,
        base_url: str,
        model: str = "gpt-4o-mini",
    ) -> "QueryTranslator":
        async def call_llm(prompt: str) -> str:
            if not api_key or not base_url:
                return "{}"
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{base_url.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 500,
                    },
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"].strip()

        return cls(call_llm=call_llm)

    async def translate_query_terms(self, query: str) -> str:
        if self._call_llm is None:
            return query
        prompt = _build_translation_prompt(query)
        try:
            content = await self._call_llm(prompt)
            match = re.search(r"\{.*\}", content, re.DOTALL)
            translations = json.loads(match.group(0)) if match else {}
        except Exception as exc:
            logger.warning("LLM term translation failed: %s", exc)
            return query
        if not translations:
            return query
        enhanced = query
        for term, english in translations.items():
            if str(english).lower() in enhanced.lower():
                continue
            if term in enhanced:
                enhanced = enhanced.replace(term, f"{term} {english} ", 1)
        return enhanced.strip()


def _build_translation_prompt(query: str) -> str:
    return f"""从以下生物学查询中提取关键术语（基因名、化合物名、通路名、生物学过程、物种名等），并翻译成对应的英文术语。

查询: {query}

要求:
1. 提取所有专业术语，忽略"的"、"在"、"中"、"如何"等虚词
2. 中文术语翻译成英文，英文术语保持原样
3. 返回 JSON 格式: {{"术语": "English term", ...}}
4. 如果查询已经是纯英文，返回空对象 {{}}

现在处理上面的查询，只返回 JSON，不要其他内容:"""


_TRANSLATOR = QueryTranslator(call_llm=None)


def configure_llm(api_key: str, base_url: str, model: str = "gpt-4o-mini"):
    global _TRANSLATOR
    _TRANSLATOR = QueryTranslator.from_openai_compatible(
        api_key=api_key,
        base_url=base_url,
        model=model,
    )


async def translate_query_terms(query: str) -> str:
    return await _TRANSLATOR.translate_query_terms(query)
