"""
共享结果渲染器 — 将统一字典结构渲染为可读文本行。

使用者：
  - 原子工具（PubmedSearchTool / GeneDBSearchTool / PersonalLibSearchTool）的 execute
    以 with_source_label=False 调用，输出不带「来源:」标签（保持各自独立工具原有格式）。
  - 聚合工具（RAGSearchTool）的 _format_results 以 with_source_label=True 调用，
    输出带「来源:」标签的聚合视图格式。

字节级兼容约束：
  rag/core/agent.py:253-357 用正则解析这些渲染结果提取引用元数据，
  任何字段名、空格、标点变化都会悄悄破坏前端参考文献提取。
  改 renderer 前务必同步核对 agent.py 的 4 个解析分支。
"""
from __future__ import annotations

from typing import Callable


def render_pubmed(item: dict, idx: int, *, with_source_label: bool) -> list[str]:
    """渲染 PubMed 一条结果为多行文本。

    独立视图（with_source_label=False）字段顺序：
        [i] {title} / 期刊: / PMID: / 链接: / 摘要: {abstract}
    聚合视图（with_source_label=True）字段顺序：
        [i] {title} / 来源: PubMed / 期刊: / PMID: / 链接: / 相关性: / 内容: {content}
    """
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
    """渲染基因数据库一条结果为多行文本。

    独立视图（with_source_label=False）字段顺序：
        [i] {title} / 基因: / 类型: / 期刊: / [DOI:]? / 相关性: / 内容:
        （独立视图没有「链接:」行）
    聚合视图（with_source_label=True）字段顺序：
        [i] {title} / 来源: 基因数据库 / 基因: / 类型: / 期刊: /
        [DOI: + 链接:]? / 相关性: / 内容:
        （聚合视图的「链接:」是嵌在 DOI 条件分支里的）
    """
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
            # 注意：原 rag_search._format_results 里「链接:」是嵌在 `if meta.get("doi")` 里的，
            # 独立视图（gene_db_search._format_results）不输出「链接:」行，保持一致。
            lines.append(f"    链接: {item.get('url', '')}")

    content = item.get("content", "")
    lines.append(f"    相关性: {item.get('score', 0.0):.4f}")
    lines.append(f"    内容: {content}")
    return lines


def render_personal(item: dict, idx: int, *, with_source_label: bool) -> list[str]:
    """渲染个人知识库一条结果为多行文本。

    独立视图（with_source_label=False）：
        [i] {filename} (p.{page})
            {content}                  ← 无 label，直接 4 空格 + 内容
    聚合视图（with_source_label=True）：
        [i] {filename} (p.{page})
            来源: 个人知识库
            相关性: {score:.4f}
            内容: {content}
    """
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


# source_type 字符串 -> renderer 的注册表。
# 注意 "personal"（不是 "personal_lib"）对齐 search/personal_lib.py:197 的历史约定。
RENDERERS: dict[str, Callable[..., list[str]]] = {
    "pubmed": render_pubmed,
    "gene_db": render_gene_db,
    "personal": render_personal,
}
