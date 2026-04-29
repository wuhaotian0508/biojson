from __future__ import annotations

import asyncio
import logging
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

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
    pubmed_query: str = ""
    gene_db_query: str = ""


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
        pubmed_query = (context.pubmed_query or query).strip()
        gene_db_query = (context.gene_db_query or query).strip()
        tasks = {
            "pubmed": self._safe_search(self.pubmed_source, pubmed_query, top_k=source_budget["pubmed"], context=context),
            "gene_db": self._safe_search(self.gene_db_source, gene_db_query, top_k=source_budget["gene_db"], context=context),
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
        warnings = self._empty_source_warnings(source_counts)

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
    def _empty_source_warnings(source_counts: dict[str, int]) -> list[str]:
        warnings = []
        if source_counts.get("pubmed") == 0:
            warnings.append("PubMed 未返回结果；如需重试，请重新调用 rag_search 并提供英文 pubmed_query。")
        if source_counts.get("gene_db") == 0:
            warnings.append("本地基因库未返回结果；如需重试，请重新调用 rag_search 并优化 query 或 gene_db_query。")
        return warnings

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
            logger.warning("%s search failed: %s: %r", source.__class__.__name__, type(exc).__name__, exc)
            return []


class PubMedSource:
    source_type = "pubmed"

    def __init__(self, *, http_client_factory=None):
        self._http_client_factory = http_client_factory or (lambda: httpx.AsyncClient(timeout=20))

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

    async def _search_raw(self, query: str, max_results: int) -> list[dict[str, Any]]:
        client = self._http_client_factory()
        close = getattr(client, "aclose", None)
        try:
            response = await client.get(
                PUBMED_ESEARCH_URL,
                params={
                    "db": "pubmed",
                    "term": query,
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
