"""
PaperTypeRouter — 根据 paper JSON 结构选择合适的 chunker。
"""
from typing import Dict, List

from utils.chunk_types import GeneChunk
from utils.chunker.base import BaseChunker
from utils.chunker.field_formatter import FieldFormatter


def _non_empty(v) -> bool:
    return not FieldFormatter._is_empty(v)


def _looks_like_linear_pathway(genes: list) -> bool:
    if not genes:
        return False
    terminals = {g.get("Terminal_Metabolite") for g in genes
                 if _non_empty(g.get("Terminal_Metabolite"))}
    pathways = {g.get("Biosynthetic_Pathway") for g in genes
                if _non_empty(g.get("Biosynthetic_Pathway"))}
    return len(terminals) <= 2 and len(pathways) <= 2


def route(paper: dict) -> str:
    has_plant = bool(paper.get("Plant_Genes"))
    has_common = bool(paper.get("Common_Genes"))
    has_pathway = bool(paper.get("Pathway_Genes"))
    has_regulation = bool(paper.get("Regulation_Genes"))

    if has_plant:
        return "plant_genes"

    # 三桶混合：pathway + regulation 同时存在，或 common + regulation 齐全
    if (has_pathway and has_regulation) or (has_common and has_regulation):
        return "mixed_bucket"

    # 纯通路链：Pathway_Genes ≥ 3，且无调控桶
    if has_pathway and not has_regulation:
        genes = paper.get("Pathway_Genes", [])
        if len(genes) >= 3 and _looks_like_linear_pathway(genes):
            return "pathway_chain"

    return "generic"


class PaperTypeRouter:
    def __init__(self, chunkers: Dict[str, BaseChunker]):
        self.chunkers = chunkers
        assert "generic" in chunkers, "必须提供 generic 兜底 chunker"

    def chunk(self, paper: dict) -> List[GeneChunk]:
        key = route(paper)
        chunker = self.chunkers.get(key) or self.chunkers["generic"]
        try:
            chunks = chunker.chunk(paper)
        except Exception as e:
            # 任何 chunker 异常都降级到 generic，保证流水线不中断
            print(f"[chunker] {key} failed on paper "
                  f"{paper.get('DOI') or paper.get('Title')}: {e}; "
                  f"falling back to generic")
            chunks = self.chunkers["generic"].chunk(paper)
        # 写入路由 key 到 metadata（便于排查）
        for c in chunks:
            if c is not None:
                c.relations.setdefault("__router__", key)
        return [c for c in chunks if c is not None]
