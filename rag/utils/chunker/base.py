"""
BaseChunker — 所有 chunker 的抽象基类和通用工具。
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from utils.chunk_types import GeneChunk
from utils.chunker.field_formatter import FieldFormatter
from utils.chunker.schemas import (
    CHUNKER_VERSION, EMPTY_VALUES,
    CHUNK_MIN_BODY_LEN, CHUNK_MAX_BODY_LEN,
)


class BaseChunker(ABC):
    chunker_key: str = "base"

    def __init__(self, formatter: FieldFormatter):
        self.fmt = formatter

    @abstractmethod
    def chunk(self, paper: dict) -> List[GeneChunk]: ...

    # ---------- 辅助构造 ----------
    def _make_chunk(self, *, paper: dict, gene: Optional[dict],
                    gene_type: str, chunk_type: str,
                    content_lines: List[str],
                    source_fields: List[str],
                    relations: Optional[dict] = None) -> Optional[GeneChunk]:
        """
        组装一个 GeneChunk。content_lines 为空 / 过短时返回 None。
        """
        body_lines = [ln for ln in content_lines if ln is not None]
        # header 行（非字段行，不进最小长度校验）
        body_text = "\n".join(body_lines).strip()
        if not body_text:
            return None
        # 粗略估算"字段行"长度（排除 header 的 [xxx] 行）
        body_len = sum(len(ln) for ln in body_lines
                       if ln and not ln.startswith("[") and not ln.startswith("── "))
        if body_len < CHUNK_MIN_BODY_LEN:
            return None
        gene_name = (gene or {}).get("Gene_Name") or "__PAPER__"
        return GeneChunk(
            gene_name=gene_name,
            paper_title=paper.get("Title") or "Unknown",
            journal=paper.get("Journal") or "Unknown",
            doi=paper.get("DOI") or "Unknown",
            gene_type=gene_type,
            content=body_text,
            metadata=gene or {},
            chunk_type=chunk_type,
            chunker_version=CHUNKER_VERSION,
            source_fields=list(source_fields),
            relations=relations or {},
        )

    # ---------- 过长拆分 ----------
    def _maybe_split(self, chunk: GeneChunk) -> List[GeneChunk]:
        """字段行过多时按 '── ' 分段拆成多个 chunk。"""
        if not chunk:
            return []
        if len(chunk.content) <= CHUNK_MAX_BODY_LEN:
            return [chunk]
        lines = chunk.content.split("\n")
        # 以 "── " 开头视为分隔
        segments: List[List[str]] = []
        header_prefix: List[str] = []
        current: List[str] = []
        header_done = False
        for ln in lines:
            if not header_done and ln.startswith("["):
                header_prefix.append(ln)
                continue
            header_done = True
            if ln.startswith("── "):
                if current:
                    segments.append(current)
                current = [ln]
            else:
                current.append(ln)
        if current:
            segments.append(current)
        if len(segments) <= 1:
            return [chunk]
        # 合并过小的相邻 segment，防止 header-only part
        merged: List[List[str]] = []
        buf: List[str] = []
        for seg in segments:
            seg_body_len = sum(len(l) for l in seg if l and not l.startswith("── "))
            if seg_body_len < CHUNK_MIN_BODY_LEN and buf:
                buf.extend(seg)
            elif seg_body_len < CHUNK_MIN_BODY_LEN and not buf:
                buf = list(seg)
            else:
                if buf:
                    # 尝试把 buf 合并到当前 seg
                    seg = buf + seg
                    buf = []
                merged.append(seg)
        if buf:
            if merged:
                merged[-1].extend(buf)
            else:
                merged.append(buf)
        segments = merged
        if len(segments) <= 1:
            # 合并后只剩一段 → 直接返回整体
            return [chunk]
        result = []
        for i, seg in enumerate(segments):
            content = "\n".join(header_prefix + seg).strip()
            if len(content) < CHUNK_MIN_BODY_LEN:
                continue
            new = GeneChunk(
                gene_name=chunk.gene_name,
                paper_title=chunk.paper_title,
                journal=chunk.journal,
                doi=chunk.doi,
                gene_type=chunk.gene_type,
                content=content,
                metadata=chunk.metadata,
                chunk_type=f"{chunk.chunk_type}__part{i+1}",
                chunker_version=chunk.chunker_version,
                source_fields=list(chunk.source_fields),
                relations=dict(chunk.relations),
            )
            result.append(new)
        return result or [chunk]

    def _postprocess(self, chunks: List[GeneChunk]) -> List[GeneChunk]:
        out: List[GeneChunk] = []
        for c in chunks:
            if c is None:
                continue
            out.extend(self._maybe_split(c))
        return out

    # ---------- 公共工具 ----------
    @staticmethod
    def _is_empty(v) -> bool:
        return FieldFormatter._is_empty(v)

    @staticmethod
    def _parse_list_field(v) -> List[str]:
        if FieldFormatter._is_empty(v):
            return []
        if isinstance(v, list):
            return [str(x).strip() for x in v if not FieldFormatter._is_empty(x)]
        return [x.strip() for x in str(v).split(";") if x.strip()]
