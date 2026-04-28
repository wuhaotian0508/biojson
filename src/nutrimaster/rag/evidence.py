from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


_INVALID_VALUES = {
    "",
    "-",
    "na",
    "n/a",
    "none",
    "null",
    "nan",
    "unknown",
    "not available",
    "not applicable",
}


def clean_text(value: object) -> str:
    text = str(value or "").strip()
    return "" if text.lower() in _INVALID_VALUES else text


def normalize_doi(value: object) -> str:
    doi = clean_text(value)
    if not doi:
        return ""
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.I).strip()
    doi = doi.removeprefix("doi:").strip()
    if doi.lower() in _INVALID_VALUES:
        return ""
    return doi


def normalize_pmid(value: object) -> str:
    pmid = clean_text(value)
    if not pmid:
        return ""
    match = re.search(r"\d+", pmid)
    return match.group(0) if match else ""


def normalize_url(value: object) -> str:
    url = clean_text(value)
    return url if re.match(r"^https?://", url, flags=re.I) else ""


def title_key(value: object) -> str:
    title = clean_text(value).lower()
    title = re.sub(r"<[^>]+>", " ", title)
    title = re.sub(r"[\W_]+", " ", title, flags=re.UNICODE)
    return re.sub(r"\s+", " ", title).strip()


def evidence_key(*, title: str, doi: str = "", pmid: str = "", url: str = "") -> tuple[str, str]:
    normalized_doi = normalize_doi(doi)
    if normalized_doi:
        return ("doi", normalized_doi.lower())
    normalized_pmid = normalize_pmid(pmid)
    if normalized_pmid:
        return ("pmid", normalized_pmid)
    normalized_url = normalize_url(url)
    if normalized_url:
        return ("url", normalized_url.rstrip("/").lower())
    return ("title", title_key(title))


@dataclass(frozen=True)
class EvidenceItem:
    source_id: str
    source_type: str
    title: str
    content: str
    url: str = ""
    doi: str = ""
    pmid: str = ""
    journal: str = ""
    gene_name: str = ""
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        doi = normalize_doi(self.doi)
        pmid = normalize_pmid(self.pmid)
        url = normalize_url(self.url)
        if not url and doi:
            url = f"https://doi.org/{doi}"
        elif not url and pmid:
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        object.__setattr__(self, "title", clean_text(self.title))
        object.__setattr__(self, "content", clean_text(self.content))
        object.__setattr__(self, "url", url)
        object.__setattr__(self, "doi", doi)
        object.__setattr__(self, "pmid", pmid)
        object.__setattr__(self, "journal", clean_text(self.journal))
        object.__setattr__(self, "gene_name", clean_text(self.gene_name))

    def to_citation(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "tool_index": int(self.source_id) if self.source_id.isdigit() else 0,
            "source_type": self.source_type,
            "title": self.title,
            "paper_title": self.title,
            "url": self.url,
            "doi": self.doi,
            "pmid": self.pmid,
            "journal": self.journal,
            "gene_name": self.gene_name,
            "score": self.score,
            "metadata": self.metadata,
        }

    def to_prompt_block(self) -> str:
        lines = [f"[{self.source_id}] {self.title}", f"来源: {self.source_type}"]
        if self.gene_name:
            lines.append(f"基因: {self.gene_name}")
        if self.journal:
            lines.append(f"期刊: {self.journal}")
        if self.doi:
            lines.append(f"DOI: {self.doi}")
        if self.pmid:
            lines.append(f"PMID: {self.pmid}")
        if self.url:
            lines.append(f"链接: {self.url}")
        lines.append(f"内容: {self.content}")
        return "\n".join(lines)


@dataclass(frozen=True)
class EvidencePacket:
    query: str
    mode: str
    items: list[EvidenceItem]
    source_counts: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    @property
    def citations(self) -> list[dict[str, Any]]:
        return [item.to_citation() for item in self.items]

    def to_tool_text(self) -> str:
        lines = [
            f"RAG 检索结果 query={self.query!r} mode={self.mode!r}",
            "要求：回答中引用这些证据时必须使用对应的 [编号]，不要自行重排编号。",
            "",
        ]
        if self.source_counts:
            counts = "；".join(f"{name}: {count}" for name, count in self.source_counts.items())
            lines.append(f"来源统计: {counts}")
        for warning in self.warnings:
            lines.append(f"注意: {warning}")
        if self.source_counts or self.warnings:
            lines.append("")
        if not self.items:
            lines.append("未找到可用证据。")
        for item in self.items:
            lines.append(item.to_prompt_block())
            lines.append("")
        return "\n".join(lines).strip()

    def __str__(self) -> str:
        return self.to_tool_text()


class EvidenceFusion:
    """Fuse source results while preserving coverage from each requested source."""

    def fuse(self, results_by_source: dict[str, list[EvidenceItem]], top_k: int) -> list[EvidenceItem]:
        nonempty = {source: items for source, items in results_by_source.items() if items}
        if not nonempty:
            return []

        output: list[EvidenceItem] = []
        for source, items in nonempty.items():
            if len(output) >= top_k:
                break
            output.append(items[0])

        candidates = [
            item
            for items in nonempty.values()
            for item in items
            if item not in output
        ]
        candidates.sort(key=lambda item: item.score, reverse=True)
        output.extend(candidates[: max(top_k - len(output), 0)])

        return self._dedupe(output)[:top_k]

    @staticmethod
    def _dedupe(items: list[EvidenceItem]) -> list[EvidenceItem]:
        output: list[EvidenceItem] = []
        seen: set[tuple[str, str]] = set()
        for item in items:
            key = evidence_key(title=item.title, doi=item.doi, pmid=item.pmid, url=item.url)
            if key == ("title", ""):
                continue
            if key in seen:
                continue
            seen.add(key)
            output.append(item)
        return output


class SourceCollector:
    """Assign stable answer-level citation numbers to fused evidence items."""

    def assign(self, items: list[EvidenceItem]) -> list[EvidenceItem]:
        output: list[EvidenceItem] = []
        seen: set[tuple[str, str]] = set()
        for item in items:
            key = evidence_key(title=item.title, doi=item.doi, pmid=item.pmid, url=item.url)
            if key == ("title", ""):
                continue
            if key in seen:
                continue
            seen.add(key)
            output.append(
                EvidenceItem(
                    source_id=str(len(output) + 1),
                    source_type=item.source_type,
                    title=item.title,
                    content=item.content,
                    url=item.url,
                    doi=item.doi,
                    pmid=item.pmid,
                    journal=item.journal,
                    gene_name=item.gene_name,
                    score=item.score,
                    metadata=item.metadata,
                )
            )
        return output


class CitationRegistry:
    """Assign citation numbers across one Agent.run lifecycle.

    Each RAG search packet is numbered locally by SourceCollector. The agent can
    call rag_search multiple times, so this registry maps repeated evidence to
    stable request-local numbers and gives new evidence the next global number.
    """

    def __init__(self) -> None:
        self._ids_by_key: dict[tuple[str, str], str] = {}

    def assign_packet(self, packet: EvidencePacket) -> EvidencePacket:
        return EvidencePacket(
            query=packet.query,
            mode=packet.mode,
            items=[self._assign_item(item) for item in packet.items],
            source_counts=packet.source_counts,
            warnings=packet.warnings,
        )

    def _assign_item(self, item: EvidenceItem) -> EvidenceItem:
        key = evidence_key(title=item.title, doi=item.doi, pmid=item.pmid, url=item.url)
        if key == ("title", ""):
            source_id = item.source_id
        else:
            source_id = self._ids_by_key.setdefault(key, str(len(self._ids_by_key) + 1))
        return EvidenceItem(
            source_id=source_id,
            source_type=item.source_type,
            title=item.title,
            content=item.content,
            url=item.url,
            doi=item.doi,
            pmid=item.pmid,
            journal=item.journal,
            gene_name=item.gene_name,
            score=item.score,
            metadata=item.metadata,
        )
