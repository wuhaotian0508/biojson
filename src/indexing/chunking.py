from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


CHUNKER_VERSION = "v2.2026-04"
CHUNK_MIN_BODY_LEN = 80
CHUNK_MAX_BODY_LEN = 1500

PLANT_FIELD_GROUPS = {
    "identity": [
        "Gene_Name",
        "Gene_Accession_Number",
        "Chromosome_Position",
        "Species",
        "Species_Latin_Name",
        "Variety",
        "Reference_Genome_Version",
        "QTL_or_Locus_Name",
    ],
    "overview": [
        "Summary_key_Findings_of_Core_Gene",
        "Summary_Key_Findings_of_Core_Gene",
        "Core_Phenotypic_Effect",
        "Research_Topic",
        "Trait_Category",
    ],
    "mechanism": [
        "Regulatory_Mechanism",
        "Regulatory_Pathway",
        "Biosynthetic_Pathway",
        "Upstream_or_Downstream_Regulation",
        "Protein_Family_or_Domain",
        "Subcellular_Localization",
        "Interacting_Proteins",
        "Expression_Pattern",
    ],
    "phenotype": [
        "Quantitative_Phenotypic_Alterations",
        "Other_Phenotypic_Effects",
        "Key_Environment_or_Treatment_Factor",
    ],
    "variant_breeding": [
        "Key_Variant_Site",
        "Key_Variant_Type",
        "Favorable_Allele",
        "Superior_Haplotype",
        "Breeding_Application_Value",
        "Field_Trials",
        "Genetic_Population",
        "Genomic_Selection_Application",
    ],
    "methods": [
        "Experimental_Methods",
        "Experimental_Materials",
        "Core_Validation_Method",
        "Gene_Discovery_or_Cloning_Method",
    ],
}

PATHWAY_FIELD_GROUPS = {
    "identity": [
        "Gene_Name",
        "Enzyme_Name",
        "EC_Number",
        "Protein_Family_or_Domain",
        "Gene_Accession_Number",
    ],
    "reaction": [
        "Primary_Substrate",
        "Primary_Product",
        "Catalyzed_Reaction_Description",
        "Biosynthetic_Pathway",
        "Pathway_Branch_or_Subpathway",
        "Metabolic_Step_Position",
        "End_Product_Connection_Type",
        "Rate_Limiting_or_Key_Control_Step",
    ],
    "terminal": [
        "Terminal_Metabolite",
        "Terminal_Metabolite_Class",
        "Terminal_Metabolite_Function",
        "Terminal_Metabolite_Accumulation_Site",
    ],
    "function": [
        "Core_Phenotypic_Effect",
        "Summary_Key_Findings_of_Core_Gene",
        "Core_Validation_Method",
        "Environment_or_Treatment_Factor",
    ],
    "interactions": ["Interacting_Proteins"],
    "engineering": [
        "Breeding_or_Engineering_Application_Value",
        "Potential_Tradeoffs",
        "Other_Important_Info",
    ],
}

REGULATION_CORE_FIELDS = [
    "Regulator_Type",
    "Regulation_Mode",
    "Primary_Regulatory_Targets",
    "Regulatory_Effect_on_Target_Genes",
    "Upstream_Signals_or_Inputs",
    "Metabolic_Process_Controlled",
    "Decisive_Influence_on_Target_Product",
    "Feedback_or_Feedforward_Regulation",
    "Protein_Complex_Involvement",
    "Epigenetic_Regulation",
]


@dataclass
class GeneChunk:
    gene_name: str
    paper_title: str
    journal: str
    doi: str
    gene_type: str
    content: str
    metadata: dict[str, Any]
    chunk_type: str = "gene"
    chunker_version: str = CHUNKER_VERSION
    source_fields: list[str] = field(default_factory=list)
    relations: dict[str, Any] = field(default_factory=dict)


class FieldFormatter:
    def __init__(self, translation: dict[str, str] | None = None):
        self.translation = translation or {}

    @classmethod
    def from_default_translation(cls, project_root: Path | None = None) -> "FieldFormatter":
        path = Path(__file__).resolve().parent / "resources" / "translate.json"
        if path.exists():
            return cls(json.loads(path.read_text(encoding="utf-8")))
        return cls()

    def render_group(
        self,
        gene: dict[str, Any],
        fields: list[str],
        section_title: str | None = None,
    ) -> list[str]:
        lines: list[str] = []
        seen_keys = set()
        for field_name in fields:
            value = gene.get(field_name)
            if self.is_empty(value):
                continue
            label = self.translation.get(field_name, field_name)
            if label in seen_keys:
                continue
            seen_keys.add(label)
            if isinstance(value, list):
                value_text = "; ".join(str(item).strip() for item in value if not self.is_empty(item))
            else:
                value_text = str(value).strip()
            if value_text:
                lines.append(f"{label}: {value_text}")
        if lines and section_title:
            return [f"── {section_title} ──", *lines]
        return lines

    @staticmethod
    def is_empty(value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() in {
                "",
                "NA",
                "na",
                "N/A",
                "null",
                "None",
                "Not established",
                "not established",
                "Unknown",
                "unknown",
            }
        return isinstance(value, list) and not value

    @staticmethod
    def header(
        paper: dict[str, Any],
        gene: dict[str, Any] | None = None,
        extras: dict[str, str] | None = None,
    ) -> list[str]:
        lines: list[str] = []
        if gene and gene.get("Gene_Name"):
            gene_header = f"[Gene] {gene['Gene_Name']}"
            if gene.get("Enzyme_Name"):
                gene_header += f"  [Enzyme] {gene['Enzyme_Name']}"
            if gene.get("Protein_Family_or_Domain"):
                gene_header += f"  [Family] {gene['Protein_Family_or_Domain']}"
            lines.append(gene_header)
        lines.append(f"[Paper] {paper.get('Title') or ''}")
        journal_line = f"[Journal] {paper.get('Journal') or ''}"
        doi = paper.get("DOI") or ""
        if doi and doi not in {"NA", "Unknown"}:
            journal_line += f"  [DOI] {doi}"
        lines.append(journal_line)
        if gene:
            species = (
                gene.get("Species_Latin_Name")
                or gene.get("Source_Species_Latin_Name")
                or gene.get("Species")
                or gene.get("Source_Species")
            )
            if species and not FieldFormatter.is_empty(species):
                lines.append(f"[Species] {species}")
        if extras:
            for key, value in extras.items():
                if not FieldFormatter.is_empty(value):
                    lines.append(f"[{key}] {value}")
        return lines


class BaseChunker:
    def __init__(self, formatter: FieldFormatter):
        self.fmt = formatter

    def _make_chunk(
        self,
        *,
        paper: dict[str, Any],
        gene: dict[str, Any] | None,
        gene_type: str,
        chunk_type: str,
        content_lines: list[str],
        source_fields: list[str],
        relations: dict[str, Any] | None = None,
    ) -> GeneChunk | None:
        content = "\n".join(line for line in content_lines if line is not None).strip()
        if not content:
            return None
        body_len = sum(
            len(line)
            for line in content.splitlines()
            if line and not line.startswith("[") and not line.startswith("── ")
        )
        if body_len < CHUNK_MIN_BODY_LEN:
            return None
        return GeneChunk(
            gene_name=(gene or {}).get("Gene_Name") or "__PAPER__",
            paper_title=paper.get("Title") or "Unknown",
            journal=paper.get("Journal") or "Unknown",
            doi=paper.get("DOI") or "Unknown",
            gene_type=gene_type,
            content=content,
            metadata=dict(gene or {}),
            chunk_type=chunk_type,
            chunker_version=CHUNKER_VERSION,
            source_fields=list(source_fields),
            relations=dict(relations or {}),
        )

    def _postprocess(self, chunks: list[GeneChunk | None]) -> list[GeneChunk]:
        output: list[GeneChunk] = []
        for chunk in chunks:
            if chunk is None:
                continue
            output.extend(self._maybe_split(chunk))
        return output

    def _maybe_split(self, chunk: GeneChunk) -> list[GeneChunk]:
        if len(chunk.content) <= CHUNK_MAX_BODY_LEN:
            return [chunk]
        return [chunk]

    @staticmethod
    def _parse_list_field(value: Any) -> list[str]:
        if FieldFormatter.is_empty(value):
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if not FieldFormatter.is_empty(item)]
        return [item.strip() for item in str(value).split(";") if item.strip()]


class GenericChunker(BaseChunker):
    def chunk(self, paper: dict[str, Any]) -> list[GeneChunk]:
        chunks = []
        for bucket in ("Pathway_Genes", "Regulation_Genes", "Common_Genes", "Plant_Genes"):
            for gene in paper.get(bucket) or []:
                chunks.append(self._one(paper, gene, bucket))
        return self._postprocess(chunks)

    def _one(self, paper: dict[str, Any], gene: dict[str, Any], bucket: str) -> GeneChunk | None:
        gene_name = gene.get("Gene_Name") or "Unknown"
        lines = [
            f"基因名称: {gene_name}",
            f"文章: {paper.get('Title') or 'Unknown'}",
            f"期刊: {paper.get('Journal') or 'Unknown'}",
            f"DOI: {paper.get('DOI') or 'Unknown'}",
            f"基因类型: {bucket}",
            "",
        ]
        source_fields = ["Gene_Name"]
        for key, value in gene.items():
            if key == "Gene_Name" or self.fmt.is_empty(value):
                continue
            if isinstance(value, list):
                value_text = "; ".join(str(item) for item in value if not self.fmt.is_empty(item))
            else:
                value_text = str(value).strip()
            if value_text:
                lines.append(f"{self.fmt.translation.get(key, key)}: {value_text}")
                source_fields.append(key)
        return GeneChunk(
            gene_name=gene_name,
            paper_title=paper.get("Title") or "Unknown",
            journal=paper.get("Journal") or "Unknown",
            doi=paper.get("DOI") or "Unknown",
            gene_type=bucket,
            content="\n".join(lines),
            metadata=dict(gene),
            chunk_type="gene",
            chunker_version=CHUNKER_VERSION,
            source_fields=source_fields,
            relations={},
        )


class PlantGenesChunker(BaseChunker):
    def chunk(self, paper: dict[str, Any]) -> list[GeneChunk]:
        chunks: list[GeneChunk | None] = []
        for gene in paper.get("Plant_Genes") or []:
            header = self.fmt.header(paper, gene)
            identity = PLANT_FIELD_GROUPS["identity"]
            overview = self.fmt.render_group(gene, PLANT_FIELD_GROUPS["overview"], "Overview")
            identity_lines = self.fmt.render_group(gene, identity, "Identity")
            chunks.append(
                self._make_chunk(
                    paper=paper,
                    gene=gene,
                    gene_type="Plant_Genes",
                    chunk_type="plant_gene_overview",
                    content_lines=header + [""] + identity_lines + [""] + overview,
                    source_fields=identity + PLANT_FIELD_GROUPS["overview"],
                )
            )
            for group_key, chunk_type, min_nonempty in (
                ("mechanism", "plant_gene_mechanism", 2),
                ("phenotype", "plant_gene_phenotype", 1),
                ("variant_breeding", "plant_gene_variant_breeding", 1),
                ("methods", "plant_gene_methods", 1),
            ):
                fields = PLANT_FIELD_GROUPS[group_key]
                if sum(1 for field_name in fields if not self.fmt.is_empty(gene.get(field_name))) < min_nonempty:
                    continue
                body = self.fmt.render_group(gene, fields, group_key.title())
                chunks.append(
                    self._make_chunk(
                        paper=paper,
                        gene=gene,
                        gene_type="Plant_Genes",
                        chunk_type=chunk_type,
                        content_lines=header + [""] + body,
                        source_fields=fields,
                    )
                )
        return self._postprocess(chunks)


class PathwayChainChunker(BaseChunker):
    def chunk(self, paper: dict[str, Any]) -> list[GeneChunk]:
        genes = paper.get("Pathway_Genes") or []
        chunks: list[GeneChunk | None] = [self._pathway_overview(paper, genes), self._pathway_graph(paper, genes)]
        chunks.extend(self._pathway_gene(paper, gene) for gene in genes)
        return self._postprocess(chunks)

    def _pathway_overview(self, paper: dict[str, Any], genes: list[dict[str, Any]]) -> GeneChunk | None:
        names = [gene.get("Gene_Name") or "?" for gene in genes]
        pathways = {gene.get("Biosynthetic_Pathway") for gene in genes if not self.fmt.is_empty(gene.get("Biosynthetic_Pathway"))}
        terminals = {gene.get("Terminal_Metabolite") for gene in genes if not self.fmt.is_empty(gene.get("Terminal_Metabolite"))}
        body = [
            "── Pathway Overview ──",
            f"通路: {'; '.join(sorted(pathways)) or 'NA'}",
            f"终产物: {'; '.join(sorted(terminals)) or 'NA'}",
            f"涉及基因 ({len(genes)}): {', '.join(names)}",
        ]
        return self._make_chunk(
            paper=paper,
            gene=None,
            gene_type="__PAPER__",
            chunk_type="pathway_overview",
            content_lines=self.fmt.header(paper) + [""] + body,
            source_fields=["Biosynthetic_Pathway", "Terminal_Metabolite", "Gene_Name"],
            relations={"pathways": list(pathways), "terminals": list(terminals), "genes": names},
        )

    def _pathway_graph(self, paper: dict[str, Any], genes: list[dict[str, Any]]) -> GeneChunk | None:
        steps = [
            f"[{gene.get('Metabolic_Step_Position') or ''}] {gene.get('Primary_Substrate') or '?'} --({gene.get('Gene_Name') or '?'})--> {gene.get('Primary_Product') or '?'}"
            for gene in genes
        ]
        return self._make_chunk(
            paper=paper,
            gene=None,
            gene_type="__PAPER__",
            chunk_type="pathway_graph",
            content_lines=self.fmt.header(paper) + ["", "── Reaction Chain ──", *steps],
            source_fields=["Primary_Substrate", "Primary_Product", "Metabolic_Step_Position", "Gene_Name"],
        )

    def _pathway_gene(self, paper: dict[str, Any], gene: dict[str, Any]) -> GeneChunk | None:
        return _pathway_gene_chunk(self, paper, gene, "Pathway_Genes", "pathway_gene")


class MixedBucketChunker(BaseChunker):
    def chunk(self, paper: dict[str, Any]) -> list[GeneChunk]:
        common = paper.get("Common_Genes") or []
        pathway = paper.get("Pathway_Genes") or []
        regulation = paper.get("Regulation_Genes") or []
        chunks: list[GeneChunk | None] = [
            self._paper_overview(paper, common, pathway, regulation),
            self._regulatory_network(paper, regulation),
        ]
        chunks.extend(_pathway_gene_chunk(self, paper, gene, "Common_Genes", "common_gene") for gene in common)
        chunks.extend(_pathway_gene_chunk(self, paper, gene, "Pathway_Genes", "pathway_gene") for gene in pathway)
        chunks.extend(self._regulation_gene(paper, gene) for gene in regulation)
        return self._postprocess(chunks)

    def _paper_overview(
        self,
        paper: dict[str, Any],
        common: list[dict[str, Any]],
        pathway: list[dict[str, Any]],
        regulation: list[dict[str, Any]],
    ) -> GeneChunk | None:
        body = ["── Gene Directory ──"]
        for label, genes in (
            ("Common_Genes", common),
            ("Pathway_Genes", pathway),
            ("Regulation_Genes", regulation),
        ):
            if genes:
                names = []
                for gene in genes:
                    name = gene.get("Gene_Name") or "?"
                    enzyme = gene.get("Enzyme_Name") or ""
                    names.append(f"{name}" + (f" ({enzyme})" if enzyme else ""))
                body.append(f"{label} ({len(genes)}): {', '.join(names)}")
        return self._make_chunk(
            paper=paper,
            gene=None,
            gene_type="__PAPER__",
            chunk_type="paper_overview",
            content_lines=self.fmt.header(paper) + [""] + body,
            source_fields=["Gene_Name"],
        )

    def _regulatory_network(self, paper: dict[str, Any], regulation: list[dict[str, Any]]) -> GeneChunk | None:
        body = ["── Regulatory Network ──"]
        regulates: dict[str, list[str]] = {}
        regulated_by: dict[str, list[str]] = {}
        for gene in regulation:
            regulator = gene.get("Gene_Name") or "?"
            targets = self._parse_list_field(gene.get("Primary_Regulatory_Targets"))
            if not targets:
                continue
            regulates[regulator] = targets
            for target in targets:
                regulated_by.setdefault(target, []).append(regulator)
            effect = gene.get("Regulatory_Effect_on_Target_Genes") or ""
            body.append(f"  {regulator} → {', '.join(targets)}" + (f" [{effect}]" if effect else ""))
        if len(body) == 1:
            return None
        return self._make_chunk(
            paper=paper,
            gene=None,
            gene_type="__PAPER__",
            chunk_type="regulatory_network",
            content_lines=self.fmt.header(paper) + [""] + body,
            source_fields=["Gene_Name", "Primary_Regulatory_Targets", "Regulatory_Effect_on_Target_Genes"],
            relations={"regulates": regulates, "regulated_by": regulated_by},
        )

    def _regulation_gene(self, paper: dict[str, Any], gene: dict[str, Any]) -> GeneChunk | None:
        header = self.fmt.header(paper, gene)
        sections = [
            self.fmt.render_group(gene, REGULATION_CORE_FIELDS, "Regulation Core"),
            self.fmt.render_group(gene, PATHWAY_FIELD_GROUPS["terminal"], "Terminal"),
            self.fmt.render_group(gene, PATHWAY_FIELD_GROUPS["function"], "Function"),
            self.fmt.render_group(gene, PATHWAY_FIELD_GROUPS["interactions"], "Interactions"),
        ]
        content = header + [""]
        for section in sections:
            if section:
                content.extend(section + [""])
        return self._make_chunk(
            paper=paper,
            gene=gene,
            gene_type="Regulation_Genes",
            chunk_type="regulation_gene",
            content_lines=content,
            source_fields=REGULATION_CORE_FIELDS + PATHWAY_FIELD_GROUPS["terminal"] + PATHWAY_FIELD_GROUPS["function"],
            relations={
                "regulates": self._parse_list_field(gene.get("Primary_Regulatory_Targets")),
                "upstream": self._parse_list_field(gene.get("Upstream_Signals_or_Inputs")),
                "interacts_with": self._parse_list_field(gene.get("Interacting_Proteins")),
            },
        )


def _pathway_gene_chunk(
    chunker: BaseChunker,
    paper: dict[str, Any],
    gene: dict[str, Any],
    gene_type: str,
    chunk_type: str,
) -> GeneChunk | None:
    header = chunker.fmt.header(paper, gene)
    sections = []
    source_fields: list[str] = []
    for group in ("reaction", "function", "interactions", "engineering"):
        fields = PATHWAY_FIELD_GROUPS[group]
        section = chunker.fmt.render_group(gene, fields, group.title())
        if section:
            sections.append(section)
            source_fields.extend(fields)
    if not sections:
        return None
    content = header + [""]
    for section in sections:
        content.extend(section)
    return chunker._make_chunk(
        paper=paper,
        gene=gene,
        gene_type=gene_type,
        chunk_type=chunk_type,
        content_lines=content,
        source_fields=source_fields,
        relations={
            "substrate": gene.get("Primary_Substrate"),
            "product": gene.get("Primary_Product"),
            "pathway": gene.get("Biosynthetic_Pathway"),
        },
    )


def _looks_like_linear_pathway(genes: list[dict[str, Any]]) -> bool:
    terminals = {
        gene.get("Terminal_Metabolite")
        for gene in genes
        if not FieldFormatter.is_empty(gene.get("Terminal_Metabolite"))
    }
    pathways = {
        gene.get("Biosynthetic_Pathway")
        for gene in genes
        if not FieldFormatter.is_empty(gene.get("Biosynthetic_Pathway"))
    }
    return len(terminals) <= 2 and len(pathways) <= 2


def route_paper(paper: dict[str, Any]) -> str:
    has_plant = bool(paper.get("Plant_Genes"))
    has_common = bool(paper.get("Common_Genes"))
    has_pathway = bool(paper.get("Pathway_Genes"))
    has_regulation = bool(paper.get("Regulation_Genes"))
    if has_plant:
        return "plant_genes"
    if (has_pathway and has_regulation) or (has_common and has_regulation):
        return "mixed_bucket"
    if has_pathway and not has_regulation:
        genes = paper.get("Pathway_Genes") or []
        if len(genes) >= 3 and _looks_like_linear_pathway(genes):
            return "pathway_chain"
    return "generic"


def chunk_paper(paper: dict[str, Any]) -> list[GeneChunk]:
    formatter = FieldFormatter.from_default_translation()
    chunkers = {
        "generic": GenericChunker(formatter),
        "plant_genes": PlantGenesChunker(formatter),
        "pathway_chain": PathwayChainChunker(formatter),
        "mixed_bucket": MixedBucketChunker(formatter),
    }
    route = route_paper(paper)
    try:
        chunks = chunkers[route].chunk(paper)
    except Exception:
        route = "generic"
        chunks = chunkers["generic"].chunk(paper)
    for chunk in chunks:
        chunk.relations.setdefault("__router__", route)
    return chunks
