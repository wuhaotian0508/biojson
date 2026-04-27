"""
MixedBucketChunker — 三桶齐全（Common + Pathway + Regulation）。

生成：
  - 1 × paper_overview          (三桶 gene 目录)
  - 1 × regulatory_network      (TF → targets + 上游 cascade + 蛋白互作)
  - Nc × common_gene
  - Np × pathway_gene           (与 PathwayChainChunker 的模板一致)
  - Nr × regulation_gene        (REGULATION_CORE_FIELDS 独占模板)
"""
from typing import List

from utils.chunk_types import GeneChunk
from utils.chunker.base import BaseChunker
from utils.chunker.schemas import (
    PATHWAY_FIELD_GROUPS, REGULATION_CORE_FIELDS,
)


class MixedBucketChunker(BaseChunker):
    chunker_key = "mixed_bucket"

    def chunk(self, paper: dict) -> List[GeneChunk]:
        chunks: List[GeneChunk] = []
        common = paper.get("Common_Genes") or []
        pathway = paper.get("Pathway_Genes") or []
        regulation = paper.get("Regulation_Genes") or []

        # 1) paper_overview
        ov = self._paper_overview(paper, common, pathway, regulation)
        if ov:
            chunks.append(ov)

        # 2) regulatory_network
        net = self._regulatory_network(paper, regulation)
        if net:
            chunks.append(net)

        # 3) per-gene chunks
        for g in common:
            c = self._common_gene(paper, g)
            if c:
                chunks.append(c)
        for g in pathway:
            c = self._pathway_gene(paper, g)
            if c:
                chunks.append(c)
        for g in regulation:
            c = self._regulation_gene(paper, g)
            if c:
                chunks.append(c)

        return self._postprocess(chunks)

    # ---------- paper overview ----------
    def _paper_overview(self, paper, common, pathway, regulation):
        header = self.fmt.header(paper)
        body = ["── Gene Directory ──"]

        def _names(lst):
            xs = []
            for g in lst:
                n = g.get("Gene_Name") or "?"
                e = g.get("Enzyme_Name") or ""
                xs.append(f"{n}" + (f" ({e})" if e else ""))
            return xs

        if common:
            body.append(f"Common_Genes ({len(common)}): {', '.join(_names(common))}")
        if pathway:
            body.append(f"Pathway_Genes ({len(pathway)}): {', '.join(_names(pathway))}")
        if regulation:
            body.append(f"Regulation_Genes ({len(regulation)}): {', '.join(_names(regulation))}")
        return self._make_chunk(
            paper=paper, gene=None,
            gene_type="__PAPER__", chunk_type="paper_overview",
            content_lines=header + [""] + body,
            source_fields=["Gene_Name"],
        )

    # ---------- regulatory network ----------
    def _regulatory_network(self, paper, regulation):
        if not regulation:
            return None
        header = self.fmt.header(paper)
        body = ["── Regulatory Network ──"]
        regulates = {}
        regulated_by = {}
        for g in regulation:
            tf = g.get("Gene_Name") or "?"
            targets = self._parse_list_field(g.get("Primary_Regulatory_Targets"))
            upstream = self._parse_list_field(g.get("Upstream_Signals_or_Inputs"))
            effect = g.get("Regulatory_Effect_on_Target_Genes") or ""
            mode = g.get("Regulation_Mode") or ""
            if targets:
                regulates[tf] = targets
                for t in targets:
                    regulated_by.setdefault(t, []).append(tf)
                body.append(f"  {tf} ({mode}) → {', '.join(targets)}"
                            + (f" [{effect}]" if effect else ""))
            if upstream:
                body.append(f"  {tf} ← upstream: {', '.join(upstream)}")
        interacts = {}
        for g in regulation:
            tf = g.get("Gene_Name") or "?"
            peers = self._parse_list_field(g.get("Interacting_Proteins"))
            if peers:
                interacts[tf] = peers
                body.append(f"  {tf} ⇄ {', '.join(peers)}")
        if len(body) == 1:  # 只有标题
            return None
        return self._make_chunk(
            paper=paper, gene=None,
            gene_type="__PAPER__", chunk_type="regulatory_network",
            content_lines=header + [""] + body,
            source_fields=["Gene_Name", "Primary_Regulatory_Targets",
                           "Upstream_Signals_or_Inputs",
                           "Regulatory_Effect_on_Target_Genes",
                           "Interacting_Proteins"],
            relations={"regulates": regulates,
                       "regulated_by": regulated_by,
                       "interacts": interacts},
        )

    # ---------- per-gene ----------
    def _common_gene(self, paper, gene):
        header = self.fmt.header(paper, gene)
        used: List[str] = []
        sections = []
        for grp in ("function", "terminal", "interactions", "engineering"):
            fields = PATHWAY_FIELD_GROUPS.get(grp, [])
            ls = self.fmt.render_group(gene, fields, section_title=grp.title())
            if ls:
                sections.append(ls)
                used.extend(fields)
        if not sections:
            return None
        content = header + [""]
        for s in sections:
            content.extend(s)
        return self._make_chunk(
            paper=paper, gene=gene,
            gene_type="Common_Genes", chunk_type="common_gene",
            content_lines=content,
            source_fields=used,
        )

    def _pathway_gene(self, paper, gene):
        header = self.fmt.header(paper, gene)
        used: List[str] = []
        sections = []
        for grp in ("reaction", "function", "interactions", "engineering"):
            fields = PATHWAY_FIELD_GROUPS.get(grp, [])
            ls = self.fmt.render_group(gene, fields, section_title=grp.title())
            if ls:
                sections.append(ls)
                used.extend(fields)
        if not sections:
            return None
        content = header + [""]
        for s in sections:
            content.extend(s)
        return self._make_chunk(
            paper=paper, gene=gene,
            gene_type="Pathway_Genes", chunk_type="pathway_gene",
            content_lines=content,
            source_fields=used,
            relations={
                "substrate": gene.get("Primary_Substrate"),
                "product": gene.get("Primary_Product"),
                "pathway": gene.get("Biosynthetic_Pathway"),
            },
        )

    def _regulation_gene(self, paper, gene):
        header = self.fmt.header(paper, gene)
        core = self.fmt.render_group(gene, REGULATION_CORE_FIELDS,
                                     section_title="Regulation Core")
        func = self.fmt.render_group(gene, PATHWAY_FIELD_GROUPS["function"],
                                     section_title="Function")
        term = self.fmt.render_group(gene, PATHWAY_FIELD_GROUPS["terminal"],
                                     section_title="Terminal")
        inter = self.fmt.render_group(gene, PATHWAY_FIELD_GROUPS["interactions"],
                                      section_title="Interactions")
        if not any([core, func, term, inter]):
            return None
        content = header + [""] + core + [""] + term + [""] + func + [""] + inter
        return self._make_chunk(
            paper=paper, gene=gene,
            gene_type="Regulation_Genes", chunk_type="regulation_gene",
            content_lines=content,
            source_fields=REGULATION_CORE_FIELDS
                          + PATHWAY_FIELD_GROUPS["terminal"]
                          + PATHWAY_FIELD_GROUPS["function"]
                          + PATHWAY_FIELD_GROUPS["interactions"],
            relations={
                "regulates": self._parse_list_field(gene.get("Primary_Regulatory_Targets")),
                "upstream": self._parse_list_field(gene.get("Upstream_Signals_or_Inputs")),
                "interacts_with": self._parse_list_field(gene.get("Interacting_Proteins")),
            },
        )
