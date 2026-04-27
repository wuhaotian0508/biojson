"""
GenericChunker — 兜底 chunker。
行为接近原 data_loader._create_gene_chunk，但接入新 GeneChunk 字段。
"""
from typing import List

from utils.chunk_types import GeneChunk
from utils.chunker.base import BaseChunker
from utils.chunker.schemas import CHUNKER_VERSION, EMPTY_VALUES


_GENE_TYPE_CN = {
    "Pathway_Genes": "代谢途径基因",
    "Regulation_Genes": "调控基因",
    "Common_Genes": "通用基因",
    "Plant_Genes": "植物基因",
}


class GenericChunker(BaseChunker):
    chunker_key = "generic"

    def chunk(self, paper: dict) -> List[GeneChunk]:
        chunks: List[GeneChunk] = []
        for bucket in ("Pathway_Genes", "Regulation_Genes",
                       "Common_Genes", "Plant_Genes"):
            genes = paper.get(bucket) or []
            for gene in genes:
                c = self._one(paper, gene, bucket)
                if c:
                    chunks.append(c)
        return self._postprocess(chunks)

    def _one(self, paper: dict, gene: dict, bucket: str):
        gene_name = gene.get("Gene_Name") or "Unknown"
        lines = [
            f"基因名称: {gene_name}",
            f"文章: {paper.get('Title') or 'Unknown'}",
            f"期刊: {paper.get('Journal') or 'Unknown'}",
            f"DOI: {paper.get('DOI') or 'Unknown'}",
            f"基因类型: {_GENE_TYPE_CN.get(bucket, bucket)}",
            "",
        ]
        src_fields = ["Gene_Name"]
        for key, value in gene.items():
            if key == "Gene_Name":
                continue
            if self._is_empty(value):
                continue
            field_name = self.fmt.translation.get(key, key)
            if isinstance(value, list):
                items = [str(v) for v in value if not self._is_empty(v)]
                if not items:
                    continue
                value_str = "; ".join(items)
            else:
                value_str = str(value).strip()
            lines.append(f"{field_name}: {value_str}")
            src_fields.append(key)
        return GeneChunk(
            gene_name=gene_name,
            paper_title=paper.get("Title") or "Unknown",
            journal=paper.get("Journal") or "Unknown",
            doi=paper.get("DOI") or "Unknown",
            gene_type=bucket,
            content="\n".join(lines),
            metadata=gene,
            chunk_type="gene",
            chunker_version=CHUNKER_VERSION,
            source_fields=src_fields,
            relations={},
        )
