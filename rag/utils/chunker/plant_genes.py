"""
PlantGenesChunker — 处理新 schema 的 Plant_Genes。

对每个 Plant_Genes[i] 生成 1~5 个 chunk：
  - plant_gene_overview        (必出; identity + overview)
  - plant_gene_mechanism       (mechanism 组 ≥ 2 非空)
  - plant_gene_phenotype       (phenotype 组 ≥ 1 非空)
  - plant_gene_variant_breeding(variant_breeding ≥ 1 非空)
  - plant_gene_methods         (methods ≥ 1 非空)
"""
from typing import List

from utils.chunk_types import GeneChunk
from utils.chunker.base import BaseChunker
from utils.chunker.schemas import PLANT_FIELD_GROUPS


class PlantGenesChunker(BaseChunker):
    chunker_key = "plant_genes"

    def chunk(self, paper: dict) -> List[GeneChunk]:
        genes = paper.get("Plant_Genes") or []
        chunks: List[GeneChunk] = []
        for gene in genes:
            chunks.extend(self._one_gene(paper, gene))
        return self._postprocess(chunks)

    def _one_gene(self, paper: dict, gene: dict) -> List[GeneChunk]:
        out: List[GeneChunk] = []
        header = self.fmt.header(paper, gene)
        identity_fields = PLANT_FIELD_GROUPS["identity"]

        # overview（必出）
        overview_lines = self.fmt.render_group(gene, PLANT_FIELD_GROUPS["overview"],
                                               section_title="Overview")
        id_lines = self.fmt.render_group(gene, identity_fields,
                                         section_title="Identity")
        content = header + [""] + id_lines + [""] + overview_lines
        c = self._make_chunk(
            paper=paper, gene=gene,
            gene_type="Plant_Genes", chunk_type="plant_gene_overview",
            content_lines=content,
            source_fields=identity_fields + PLANT_FIELD_GROUPS["overview"],
        )
        if c:
            out.append(c)

        # 其余分组
        for group_key, chunk_type, min_nonempty in (
            ("mechanism", "plant_gene_mechanism", 2),
            ("phenotype", "plant_gene_phenotype", 1),
            ("variant_breeding", "plant_gene_variant_breeding", 1),
            ("methods", "plant_gene_methods", 1),
        ):
            fields = PLANT_FIELD_GROUPS[group_key]
            non_empty = sum(1 for f in fields if not self._is_empty(gene.get(f)))
            if non_empty < min_nonempty:
                continue
            body = self.fmt.render_group(gene, fields,
                                         section_title=group_key.title())
            content = header + [""] + body
            c = self._make_chunk(
                paper=paper, gene=gene,
                gene_type="Plant_Genes", chunk_type=chunk_type,
                content_lines=content,
                source_fields=fields,
            )
            if c:
                out.append(c)
        return out
