"""
PathwayChainChunker — 纯通路链论文。

生成：
  - 1 × pathway_overview   (通路 + 源物种 + 终产物 + gene 列表)
  - 1 × pathway_graph      (反应链拼接，按 Metabolic_Step_Position 排序)
  - N × pathway_gene       (每个酶的 reaction + function + interactions + engineering)
"""
from typing import List

from utils.chunk_types import GeneChunk
from utils.chunker.base import BaseChunker
from utils.chunker.schemas import PATHWAY_FIELD_GROUPS


_STEP_ORDER = {
    "upstream": 0, "early": 0,
    "midstream": 1, "middle": 1, "mid": 1,
    "downstream": 2, "late": 2, "terminal": 2, "final": 2,
}


def _step_key(pos: str) -> int:
    if not pos:
        return 1
    s = str(pos).lower()
    for k, v in _STEP_ORDER.items():
        if k in s:
            return v
    return 1


class PathwayChainChunker(BaseChunker):
    chunker_key = "pathway_chain"

    def chunk(self, paper: dict) -> List[GeneChunk]:
        genes = paper.get("Pathway_Genes") or []
        if not genes:
            return []
        chunks: List[GeneChunk] = []

        # 1) pathway_overview
        ov = self._pathway_overview(paper, genes)
        if ov:
            chunks.append(ov)

        # 2) pathway_graph
        gr = self._pathway_graph(paper, genes)
        if gr:
            chunks.append(gr)

        # 3) pathway_gene × N
        for gene in genes:
            c = self._pathway_gene(paper, gene)
            if c:
                chunks.append(c)

        return self._postprocess(chunks)

    # ---------------- overview ----------------
    def _pathway_overview(self, paper: dict, genes: list) -> GeneChunk | None:
        terminals = {g.get("Terminal_Metabolite") for g in genes
                     if not self._is_empty(g.get("Terminal_Metabolite"))}
        pathways = {g.get("Biosynthetic_Pathway") for g in genes
                    if not self._is_empty(g.get("Biosynthetic_Pathway"))}
        species = {g.get("Source_Species") for g in genes
                   if not self._is_empty(g.get("Source_Species"))}

        gene_list = []
        for g in genes:
            n = g.get("Gene_Name") or "?"
            enzyme = g.get("Enzyme_Name") or ""
            gene_list.append(f"{n}" + (f" ({enzyme})" if enzyme else ""))

        header = self.fmt.header(paper)
        body = [
            "── Pathway Overview ──",
            f"通路: {'; '.join(sorted(pathways)) or 'NA'}",
            f"源物种: {'; '.join(sorted(species)) or 'NA'}",
            f"终产物: {'; '.join(sorted(terminals)) or 'NA'}",
            f"涉及基因 ({len(genes)}): {', '.join(gene_list)}",
        ]
        return self._make_chunk(
            paper=paper, gene=None,
            gene_type="__PAPER__", chunk_type="pathway_overview",
            content_lines=header + [""] + body,
            source_fields=["Biosynthetic_Pathway", "Source_Species",
                           "Terminal_Metabolite", "Gene_Name"],
            relations={"pathways": list(pathways),
                       "terminals": list(terminals),
                       "genes": [g.get("Gene_Name") for g in genes]},
        )

    # ---------------- graph ----------------
    def _pathway_graph(self, paper: dict, genes: list) -> GeneChunk | None:
        sorted_genes = sorted(genes, key=lambda g: _step_key(g.get("Metabolic_Step_Position")))
        steps = []
        for g in sorted_genes:
            sub = g.get("Primary_Substrate") or "?"
            prod = g.get("Primary_Product") or "?"
            name = g.get("Gene_Name") or "?"
            pos = g.get("Metabolic_Step_Position") or ""
            steps.append(f"[{pos}] {sub} --({name})--> {prod}")
        if not steps:
            return None
        header = self.fmt.header(paper)
        body = ["── Reaction Chain ──"] + steps
        # 分支酶
        branches = []
        for g in sorted_genes:
            conn = g.get("End_Product_Connection_Type") or ""
            if any(k in str(conn).lower() for k in ("branch", "compet", "alternat")):
                branches.append(f"  • {g.get('Gene_Name')}: {conn}")
        if branches:
            body.append("── Branch points ──")
            body.extend(branches)
        return self._make_chunk(
            paper=paper, gene=None,
            gene_type="__PAPER__", chunk_type="pathway_graph",
            content_lines=header + [""] + body,
            source_fields=["Primary_Substrate", "Primary_Product",
                           "Metabolic_Step_Position",
                           "End_Product_Connection_Type", "Gene_Name"],
        )

    # ---------------- per-gene ----------------
    def _pathway_gene(self, paper: dict, gene: dict) -> GeneChunk | None:
        header = self.fmt.header(paper, gene)
        # reaction 组靠前
        sections = []
        used_fields: List[str] = []
        for grp in ("reaction", "function", "interactions", "engineering"):
            fields = PATHWAY_FIELD_GROUPS[grp]
            lines = self.fmt.render_group(gene, fields, section_title=grp.title())
            if lines:
                sections.append(lines)
                used_fields.extend(fields)
        if not sections:
            return None
        content_lines = header + [""]
        for sec in sections:
            content_lines.extend(sec)
        return self._make_chunk(
            paper=paper, gene=gene,
            gene_type="Pathway_Genes", chunk_type="pathway_gene",
            content_lines=content_lines,
            source_fields=used_fields,
            relations={
                "substrate": gene.get("Primary_Substrate"),
                "product": gene.get("Primary_Product"),
                "pathway": gene.get("Biosynthetic_Pathway"),
                "interacts_with": self._parse_list_field(gene.get("Interacting_Proteins")),
            },
        )
