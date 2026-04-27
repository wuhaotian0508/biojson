"""
Chunker 模块 — 将论文 JSON 转成向量检索用的 GeneChunk 列表。

外部调用：
    from utils.chunker import chunk_paper
    chunks = chunk_paper(paper_dict)

内部分型：
    PaperTypeRouter 根据 JSON 结构选择 chunker：
      - PlantGenesChunker   (Plant_Genes)
      - PathwayChainChunker (纯通路链)
      - MixedBucketChunker  (三桶混合)
      - GenericChunker      (兜底)

详见 CHUNKER_IMPLEMENTATION_PLAN.md
"""
from typing import List, Optional
from utils.chunker.router import PaperTypeRouter
from utils.chunker.field_formatter import FieldFormatter
from utils.chunker.generic import GenericChunker
from utils.chunker.plant_genes import PlantGenesChunker
from utils.chunker.pathway_chain import PathwayChainChunker
from utils.chunker.mixed_bucket import MixedBucketChunker
from utils.chunk_types import GeneChunk

# 惰性初始化全局 formatter / chunker 实例
_ROUTER: Optional[PaperTypeRouter] = None


def _get_router() -> PaperTypeRouter:
    global _ROUTER
    if _ROUTER is None:
        fmt = FieldFormatter.from_default_translation()
        _ROUTER = PaperTypeRouter(
            chunkers={
                "generic": GenericChunker(fmt),
                "plant_genes": PlantGenesChunker(fmt),
                "pathway_chain": PathwayChainChunker(fmt),
                "mixed_bucket": MixedBucketChunker(fmt),
            }
        )
    return _ROUTER


def chunk_paper(paper: dict) -> List[GeneChunk]:
    """对一篇 paper JSON 生成 chunk 列表。"""
    router = _get_router()
    return router.chunk(paper)


__all__ = ["chunk_paper", "GeneChunk", "PaperTypeRouter"]
