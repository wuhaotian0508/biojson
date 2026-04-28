from __future__ import annotations

from collections.abc import Callable


def render_pubmed(item: dict, idx: int, *, with_source_label: bool) -> list[str]:
    meta = item.get("metadata", {})
    lines = [f"[{idx}] {item.get('title', '')}"]
    if with_source_label:
        lines.append("    来源: PubMed")
    lines.append(f"    期刊: {meta.get('journal', '')}")
    lines.append(f"    PMID: {meta.get('pmid', '')}")
    lines.append(f"    链接: {item.get('url', '')}")
    content = item.get("content", "")
    if with_source_label:
        lines.append(f"    相关性: {item.get('score', 0.0):.4f}")
        lines.append(f"    内容: {content}")
    else:
        lines.append(f"    摘要: {content}")
    return lines


def render_gene_db(item: dict, idx: int, *, with_source_label: bool) -> list[str]:
    meta = item.get("metadata", {})
    lines = [f"[{idx}] {item.get('title', '')}"]
    if with_source_label:
        lines.append("    来源: 基因数据库")
    lines.append(f"    基因: {meta.get('gene_name', '')}")
    lines.append(f"    类型: {meta.get('gene_type', '')}")
    lines.append(f"    期刊: {meta.get('journal', '')}")
    if meta.get("doi"):
        lines.append(f"    DOI: {meta['doi']}")
        if with_source_label:
            lines.append(f"    链接: {item.get('url', '')}")
    lines.append(f"    相关性: {item.get('score', 0.0):.4f}")
    lines.append(f"    内容: {item.get('content', '')}")
    return lines


def render_personal(item: dict, idx: int, *, with_source_label: bool) -> list[str]:
    meta = item.get("metadata", {})
    filename = meta.get("filename", "")
    page = meta.get("page", "")
    lines = [f"[{idx}] {filename} (p.{page})"]
    content = item.get("content", "")
    if with_source_label:
        lines.append("    来源: 个人知识库")
        lines.append(f"    相关性: {item.get('score', 0.0):.4f}")
        lines.append(f"    内容: {content}")
    else:
        lines.append(f"    {content}")
    return lines


RENDERERS: dict[str, Callable[..., list[str]]] = {
    "pubmed": render_pubmed,
    "gene_db": render_gene_db,
    "personal": render_personal,
}
