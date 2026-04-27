"""
Query 规则扩写模块（方案 B1）

对用户原始 query 做规则扩写，解决以下问题：
  1. 跨语言词汇鸿沟：中文 query × 英文 chunk（利用双语术语词典）
  2. 希腊字母互转：α ↔ alpha、β ↔ beta
  3. 立体化学描述符归一：25S/25R 追加英文格式变体

用法：
    from search.query_expander import expand_query
    queries = expand_query("α-番茄碱与 α-澳洲茄胺的生物学功能")
    # → ["α-番茄碱与 α-澳洲茄胺的生物学功能",
    #     "α-番茄碱 α-tomatine 与 α-澳洲茄胺 α-solamargine 的生物学功能"]
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import List, Dict

# ===== 加载双语词汇表 =====
_GLOSSARY_PATH = Path(__file__).resolve().parent.parent / "config" / "bilingual_glossary.json"

def _load_glossary() -> Dict[str, str]:
    """加载双语词汇表，返回 {中文: 英文} 映射。"""
    if not _GLOSSARY_PATH.exists():
        return {}
    with open(_GLOSSARY_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    mapping: Dict[str, str] = {}
    for section_val in raw.values():
        if isinstance(section_val, dict):
            for zh, en in section_val.items():
                if zh != "comment":
                    mapping[zh] = en
    return mapping

_GLOSSARY: Dict[str, str] = _load_glossary()

# 反向映射：英文 → 中文（小写键）
_GLOSSARY_EN2ZH: Dict[str, str] = {en.lower(): zh for zh, en in _GLOSSARY.items()}

# ===== 希腊字母互转 =====
_GREEK_MAP = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta",
    "ε": "epsilon", "ζ": "zeta", "η": "eta", "θ": "theta",
    "κ": "kappa", "λ": "lambda", "μ": "mu", "ν": "nu",
    "ξ": "xi", "π": "pi", "ρ": "rho", "σ": "sigma",
    "τ": "tau", "φ": "phi", "χ": "chi", "ψ": "psi", "ω": "omega",
}
_GREEK_REVERSE = {v: k for k, v in _GREEK_MAP.items()}

# ===== 立体描述符正则 =====
_STEREO_PATTERN = re.compile(r"\b(25[SR]|2[SR]|[RSEZ])-")


def _expand_bilingual(query: str) -> str:
    """
    将 query 中出现的中文术语追加英文翻译，英文术语追加中文翻译。
    例：
      "α-番茄碱的功能" → "α-番茄碱 α-tomatine 的功能"
    """
    q = unicodedata.normalize("NFKC", query)

    # 中 → 英
    for zh, en in sorted(_GLOSSARY.items(), key=lambda x: -len(x[0])):
        if zh in q and en.lower() not in q.lower():
            q = q.replace(zh, f"{zh} {en}", 1)

    # 英 → 中（只对孤立的英文词做追加，避免已有中文时重复）
    for en_lower, zh in sorted(_GLOSSARY_EN2ZH.items(), key=lambda x: -len(x[0])):
        pattern = re.compile(re.escape(en_lower), re.IGNORECASE)
        if pattern.search(q) and zh not in q:
            q = pattern.sub(lambda m: f"{m.group(0)} {zh}", q, count=1)

    return q


def _expand_greek(query: str) -> str:
    """
    希腊字母互转：
      "α-tomatine" → "alpha-tomatine"（仅在没有 alpha 变体时追加）
    """
    result = query
    for greek, latin in _GREEK_MAP.items():
        if greek in result and latin not in result:
            result = result + f" {result.replace(greek, latin)}"
    return result


def _expand_stereo(query: str) -> str:
    """
    立体化学描述符补全：
      "25S 构型" → "25S 构型 (25S)- 25S-"
    """
    result = query
    for m in _STEREO_PATTERN.finditer(query):
        code = m.group(1)  # e.g. "25S"
        for fmt in [f"({code})-", f"{code}-configured"]:
            if fmt not in result:
                result += f" {fmt}"
    return result


def expand_query(query: str) -> List[str]:
    """
    规则扩写主入口，返回多个 query 变体（包括原始 query）。

    变体列表：
      0. 原始 query（不做任何修改，保证覆盖原始词形）
      1. 双语扩写版本（中英互补）
      2. 希腊字母扩写版本（叠加在双语版本基础上）
      3. 立体描述符扩写版本（若存在 25S/25R 等时才生成）

    重复的变体会自动去重。
    """
    variants: List[str] = [query]

    # 1. 双语扩写
    bilingual = _expand_bilingual(query)
    if bilingual != query:
        variants.append(bilingual)

    # 2. 希腊字母（基于双语版本继续扩）
    base = bilingual if bilingual != query else query
    greek = _expand_greek(base)
    if greek != base and greek not in variants:
        variants.append(greek)

    # 3. 立体描述符
    stereo = _expand_stereo(base)
    if stereo != base and stereo not in variants:
        variants.append(stereo)

    return variants


if __name__ == "__main__":
    test_queries = [
        "α-番茄碱与 α-澳洲茄胺的生物学功能",
        "25S 构型与 25R 构型生物碱差异",
        "GAME8 gene function in tomato alkaloid biosynthesis",
        "类胡萝卜素合成通路关键酶",
    ]
    for q in test_queries:
        print(f"\nOriginal: {q}")
        for i, v in enumerate(expand_query(q)):
            print(f"  [{i}] {v}")
