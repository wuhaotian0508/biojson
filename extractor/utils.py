"""
utils.py — Shared utilities for the extractor pipeline.

Consolidates repeated patterns found across extract.py, verify.py, and pipeline.py.

[PR 新增文件 by 学长 muskliu - 2026-03-29]
这个文件是学长新建的，把原来散落在 extract.py 和 verify.py 中的工具函数提取出来：
- GENE_ARRAY_KEYS / GENE_ARRAY_KEY_NAMES：基因数组的 key 常量，原来在多处硬编码
- ensure_list()：防御性地把值转成 list，原来在 extract.py 中
- get_gene_name()：从基因 dict 中提取名字（兼容多种 key），原来在 extract.py 中
- safe_parse_json()：JSON 解析 + 截断修复，原来是 extract.py 中的 _safe_parse_json()
- stem_to_dirname()：文件名转目录名，原来是 extract.py 中的私有函数
目的：消除 verify.py 从 extract.py 导入私有函数的跨模块耦合
"""

import json
from typing import Optional

# ─── Gene array key constants ────────────────────────────────────────────────

GENE_ARRAY_KEYS = (
    ("Common_Genes", "Common"),
    ("Pathway_Genes", "Pathway"),
    ("Regulation_Genes", "Regulation"),
)

GENE_ARRAY_KEY_NAMES = tuple(k for k, _ in GENE_ARRAY_KEYS)


# ─── Defensive parsing helpers ───────────────────────────────────────────────

def ensure_list(val) -> list:
    """Convert a value to a list, handling str→json.loads and type mismatches."""
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
        return []
    return []


def get_gene_name(gene_dict: dict) -> str:
    """Extract gene name from a gene dict, trying multiple key variants."""
    return (
        gene_dict.get("Gene_Name")
        or gene_dict.get("gene")
        or gene_dict.get("gene_name")
        or gene_dict.get("name")
        or ""
    )


def safe_parse_json(json_str: str, label: str = "") -> Optional[dict]:
    """Parse JSON with truncation repair.

    Tries direct parse first, then attempts to fix truncated JSON by
    balancing braces and brackets.
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    last_brace = json_str.rfind('}')
    if last_brace == -1:
        return None

    truncated = json_str[:last_brace + 1]
    ob = truncated.count('{') - truncated.count('}')
    obr = truncated.count('[') - truncated.count(']')
    repair = truncated + ']' * max(0, obr) + '}' * max(0, ob)
    try:
        result = json.loads(repair)
        if label:
            print(f"    🔧 [{label}] Truncated JSON auto-repaired")
        return result
    except json.JSONDecodeError:
        return None


def stem_to_dirname(stem: str) -> str:
    """Convert a filename stem to a directory name.

    Strips MinerU prefix, removes '_(1)' duplicates, replaces '_' with '-'.
    """
    if stem.startswith("MinerU_markdown_"):
        stem = stem[len("MinerU_markdown_"):]
    stem = stem.replace("_(1)", "")
    stem = stem.replace("_", "-")
    return stem
