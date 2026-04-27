"""
GeneChunk 数据类 — 向量检索的最小单元。

扩展自原 data_loader.GeneChunk，新增：
  - chunk_type / chunker_version / source_fields
  - relations（结构化关系，供图式扩展）

为保持向后兼容，老代码 `from utils.data_loader import GeneChunk` 仍可用
（data_loader.py 会重新导出本模块的 GeneChunk）。
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class GeneChunk:
    # ── 原有字段（保持不变） ──
    gene_name: str
    paper_title: str
    journal: str
    doi: str
    gene_type: str                     # Common_Genes / Pathway_Genes / Regulation_Genes / Plant_Genes / __PAPER__
    content: str
    metadata: Dict[str, Any]

    # ── 新增字段 ──
    chunk_type: str = "gene"           # paper_overview / pathway_gene / regulation_gene / plant_gene_* / ...
    chunker_version: str = "v1-legacy"
    source_fields: List[str] = field(default_factory=list)
    relations: Dict[str, Any] = field(default_factory=dict)
