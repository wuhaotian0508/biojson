from __future__ import annotations

import re

_GENE_NAME_RE = re.compile(r"\b[A-Z][a-z]{1,2}[A-Z][A-Za-z]{0,10}\d{0,3}[A-Za-z]?\b")
_TOOL_NAME_BLACKLIST = {
    "SpCas9",
    "SaCas9",
    "FnCas12a",
    "LbCpf1",
    "AsCpf1",
    "CasRx",
    "dCas9",
    "nCas9",
    "Cas12a",
    "Cas13a",
    "PubMed",
}
_VAGUE_SUFFIXES = ("之类", "之类的", "等", "等等", "类似")


def has_gene_names(text: str) -> bool:
    return bool(extract_gene_names(text))


def extract_gene_names(text: str) -> list[str]:
    seen = set()
    names = []
    for match in _GENE_NAME_RE.finditer(text):
        name = match.group()
        if name in _TOOL_NAME_BLACKLIST:
            continue
        suffix = text[match.end():]
        if any(suffix.startswith(item) for item in _VAGUE_SUFFIXES):
            continue
        if name not in seen:
            seen.add(name)
            names.append(name)
    return names
