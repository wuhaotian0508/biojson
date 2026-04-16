"""
植物基因名检测与提取工具（从 skill_loader.py 抽取）

供 SOP 流程等需要从文本中识别基因名的场景使用。
"""
from __future__ import annotations

import re

# ---- 植物基因名正则模式 ----
_GENE_NAME_RE = re.compile(r'\b[A-Z][a-z]{1,2}[A-Z][A-Za-z]{0,10}\d{0,3}[A-Za-z]?\b')

# ---- CRISPR 工具/酶名称黑名单 ----
_TOOL_NAME_BLACKLIST = {
    "SpCas9", "SaCas9", "FnCas12a", "LbCpf1", "AsCpf1",
    "CasRx", "dCas9", "nCas9", "Cas12a", "Cas13a", "PubMed",
}

# ---- 模糊后缀 ----
_VAGUE_SUFFIXES = ("之类", "之类的", "等", "等等", "类似")


def has_gene_names(text: str) -> bool:
    """检测文本中是否包含具体的植物基因名"""
    for m in _GENE_NAME_RE.finditer(text):
        name = m.group()
        if name in _TOOL_NAME_BLACKLIST:
            continue
        after = text[m.end():]
        if any(after.startswith(s) for s in _VAGUE_SUFFIXES):
            continue
        return True
    return False


def extract_gene_names(text: str) -> list[str]:
    """从文本中提取所有具体的植物基因名（去重，保持出现顺序）"""
    seen = set()
    gene_names = []
    for m in _GENE_NAME_RE.finditer(text):
        name = m.group()
        if name in _TOOL_NAME_BLACKLIST:
            continue
        after = text[m.end():]
        if any(after.startswith(s) for s in _VAGUE_SUFFIXES):
            continue
        if name not in seen:
            seen.add(name)
            gene_names.append(name)
    return gene_names
