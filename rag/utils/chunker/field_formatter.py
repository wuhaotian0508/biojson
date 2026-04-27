"""
FieldFormatter — 字段清洗 / 翻译 / 格式化工具。
"""
import json
from pathlib import Path
from typing import Dict, List, Optional


class FieldFormatter:
    def __init__(self, translation: Optional[Dict[str, str]] = None):
        self.translation = translation or {}

    @classmethod
    def from_default_translation(cls) -> "FieldFormatter":
        """从 rag/translate.json 读取翻译表。"""
        try:
            import core.config as config
            p = config.PROJECT_ROOT / "translate.json"
        except Exception:
            p = Path(__file__).resolve().parents[2] / "translate.json"
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return cls(translation=json.load(f))
        return cls(translation={})

    # ---------- 字段渲染 ----------
    def render_group(self, gene: dict, fields: List[str],
                     section_title: Optional[str] = None) -> List[str]:
        """渲染一个字段组，自动过滤空值、翻译字段名、去重。"""
        lines: List[str] = []
        seen_keys = set()   # 避免 overview 里同名字段重复（兼容两种拼写）
        for field in fields:
            value = gene.get(field)
            if self._is_empty(value):
                continue
            key = self.translation.get(field, field)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            if isinstance(value, list):
                items = [str(v).strip() for v in value if not self._is_empty(v)]
                if not items:
                    continue
                value_str = "; ".join(items)
            else:
                value_str = str(value).strip()
            lines.append(f"{key}: {value_str}")
        if lines and section_title:
            lines = [f"── {section_title} ──"] + lines
        return lines

    @staticmethod
    def _is_empty(v) -> bool:
        if v is None:
            return True
        if isinstance(v, str):
            s = v.strip()
            if s in ("", "NA", "na", "N/A", "null", "None",
                     "Not established", "not established",
                     "Unknown", "unknown"):
                return True
        if isinstance(v, list) and len(v) == 0:
            return True
        return False

    # ---------- header ----------
    @staticmethod
    def header(paper: dict, gene: Optional[dict] = None,
               extras: Optional[Dict[str, str]] = None) -> List[str]:
        lines: List[str] = []
        if gene and gene.get("Gene_Name"):
            gene_hdr = f"[Gene] {gene['Gene_Name']}"
            if gene.get("Enzyme_Name"):
                gene_hdr += f"  [Enzyme] {gene['Enzyme_Name']}"
            if gene.get("Protein_Family_or_Domain"):
                gene_hdr += f"  [Family] {gene['Protein_Family_or_Domain']}"
            lines.append(gene_hdr)
        title = paper.get("Title") or ""
        journal = paper.get("Journal") or ""
        doi = paper.get("DOI") or ""
        lines.append(f"[Paper] {title}")
        meta = f"[Journal] {journal}"
        if doi and doi not in ("NA", "Unknown", ""):
            meta += f"  [DOI] {doi}"
        lines.append(meta)
        if gene:
            species = (gene.get("Species_Latin_Name")
                       or gene.get("Source_Species_Latin_Name")
                       or gene.get("Species")
                       or gene.get("Source_Species"))
            if species and not FieldFormatter._is_empty(species):
                lines.append(f"[Species] {species}")
        if extras:
            for k, v in extras.items():
                if not FieldFormatter._is_empty(v):
                    lines.append(f"[{k}] {v}")
        return lines
