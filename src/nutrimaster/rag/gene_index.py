from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import pickle
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger("indexer")

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


def sha256_of(path: Path, buf_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        while chunk := file.read(buf_size):
            digest.update(chunk)
    return digest.hexdigest()


class IncrementalIndexer:
    def __init__(
        self,
        index_dir: Path,
        data_dir: Path,
        embed_fn: Callable[[list[str]], np.ndarray],
        file_pattern: str = "*.json",
    ):
        self.index_dir = Path(index_dir)
        self.data_dir = Path(data_dir)
        self.embed_fn = embed_fn
        self.file_pattern = file_pattern
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_path = self.index_dir / "chunks.pkl"
        self.embeds_path = self.index_dir / "embeddings.npy"
        self.manifest_path = self.index_dir / "manifest.json"

    def monitor_on_startup(self):
        logger.info(
            "[monitor] data_dir=%s verified JSON=%d",
            self.data_dir,
            len(list(self.data_dir.glob(self.file_pattern))),
        )

    def build_incremental(self, *, force: bool = False, batch_embed_size: int = 32, load_paper_fn=None):
        load_paper_fn = load_paper_fn or self._load_paper
        files = sorted(self.data_dir.glob(self.file_pattern))
        manifest = {} if force else self._load_manifest()
        old_chunks, old_embeddings = ([], None) if force else self._load_existing()
        if not self._manifest_reusable(manifest, old_chunks, old_embeddings):
            manifest = {}
            old_chunks, old_embeddings = [], None

        file_shas = {path.name: sha256_of(path) for path in files}
        to_keep = []
        to_rebuild = []
        for path in files:
            entry = manifest.get(path.name)
            if (
                entry
                and entry.get("sha") == file_shas[path.name]
                and entry.get("chunker_version") == CHUNKER_VERSION
            ):
                to_keep.append(path.name)
            else:
                to_rebuild.append(path)

        final_chunks: list[GeneChunk] = []
        final_embedding_parts = []
        new_manifest = {}
        cursor = 0

        for name in to_keep:
            entry = manifest[name]
            start = int(entry["start"])
            end = int(entry["end"])
            chunks = old_chunks[start:end]
            final_chunks.extend(chunks)
            if old_embeddings is not None:
                final_embedding_parts.append(old_embeddings[start:end])
            new_manifest[name] = {
                "sha": entry["sha"],
                "chunker_version": CHUNKER_VERSION,
                "n_chunks": len(chunks),
                "start": cursor,
                "end": cursor + len(chunks),
            }
            cursor += len(chunks)

        for path in to_rebuild:
            chunks = load_paper_fn(path) or []
            embeddings = self.embed_fn([chunk.content for chunk in chunks]) if chunks else None
            if embeddings is not None and embeddings.shape[0] != len(chunks):
                raise RuntimeError("embedding count does not match chunk count")
            start = cursor
            final_chunks.extend(chunks)
            cursor += len(chunks)
            if embeddings is not None:
                final_embedding_parts.append(embeddings)
            new_manifest[path.name] = {
                "sha": file_shas[path.name],
                "chunker_version": CHUNKER_VERSION,
                "n_chunks": len(chunks),
                "start": start,
                "end": cursor,
            }

        final_embeddings = None
        if final_embedding_parts:
            final_embeddings = (
                np.concatenate(final_embedding_parts, axis=0)
                if len(final_embedding_parts) > 1
                else final_embedding_parts[0]
            )
        if final_chunks and final_embeddings is None:
            raise RuntimeError("chunks exist but embeddings are missing")
        if final_embeddings is not None and final_embeddings.shape[0] != len(final_chunks):
            raise RuntimeError("final embeddings do not match chunks")

        self._save(final_chunks, final_embeddings, new_manifest)
        return final_chunks, final_embeddings

    def _load_paper(self, path: Path) -> list[GeneChunk]:
        return chunk_paper(json.loads(Path(path).read_text(encoding="utf-8")))

    def _load_manifest(self) -> dict:
        if not self.manifest_path.exists():
            return {}
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            if data.get("chunker_version") != CHUNKER_VERSION:
                return {}
            return data.get("files", {})
        except Exception:
            return {}

    def _load_existing(self):
        if not (self.chunks_path.exists() and self.embeds_path.exists()):
            return [], None
        try:
            with self.chunks_path.open("rb") as file:
                chunks = pickle.load(file)
            embeddings = np.load(self.embeds_path)
            if len(chunks) != embeddings.shape[0]:
                return [], None
            return chunks, embeddings
        except Exception:
            return [], None

    @staticmethod
    def _manifest_reusable(manifest: dict, chunks: list, embeddings) -> bool:
        if not manifest:
            return True
        if embeddings is None:
            return False
        expected_total = 0
        for entry in manifest.values():
            start = int(entry.get("start", -1))
            end = int(entry.get("end", -1))
            n_chunks = int(entry.get("n_chunks", end - start))
            if start < 0 or end < start or n_chunks != end - start:
                return False
            expected_total = max(expected_total, end)
        return len(chunks) >= expected_total and embeddings.shape[0] >= expected_total

    def _save(self, chunks: list[GeneChunk], embeddings, manifest_files: dict):
        with self.chunks_path.open("wb") as file:
            pickle.dump(chunks, file)
        if embeddings is not None:
            np.save(self.embeds_path, embeddings)
        elif self.embeds_path.exists():
            self.embeds_path.unlink()
        self.manifest_path.write_text(
            json.dumps(
                {"chunker_version": CHUNKER_VERSION, "files": manifest_files},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


@dataclass(frozen=True)
class IndexBuildResult:
    """Summary returned by the index service after a build."""

    chunk_count: int
    embedding_shape: tuple[int, ...] | None
    data_dir: Path
    index_dir: Path


class IndexService:
    """Canonical indexing boundary while legacy RAG modules are being strangled."""

    def __init__(
        self,
        *,
        data_dir: Path,
        index_dir: Path,
        embed_texts: Callable[[list[str]], np.ndarray],
        load_paper: Callable[[Path], list[Any]] | None = None,
        indexer_cls: type | None = None,
    ):
        self.data_dir = Path(data_dir)
        self.index_dir = Path(index_dir)
        self.embed_texts = embed_texts
        self.load_paper = load_paper
        self.indexer_cls = indexer_cls

    def build(self, *, force: bool = False) -> IndexBuildResult:
        indexer_cls = self.indexer_cls or IncrementalIndexer
        load_paper = self.load_paper or self._load_paper_chunks

        indexer = indexer_cls(
            index_dir=self.index_dir,
            data_dir=self.data_dir,
            embed_fn=self.embed_texts,
        )
        chunks, embeddings = indexer.build_incremental(
            force=force,
            load_paper_fn=load_paper,
        )
        return IndexBuildResult(
            chunk_count=len(chunks),
            embedding_shape=None if embeddings is None else tuple(embeddings.shape),
            data_dir=self.data_dir,
            index_dir=self.index_dir,
        )

    @staticmethod
    def _load_paper_chunks(path: Path) -> list[Any]:
        with Path(path).open("r", encoding="utf-8") as file:
            paper = json.load(file)
        return chunk_paper(paper)


class RetrievalService:
    """Tool-neutral retrieval boundary around the current gene retriever."""

    def __init__(self, *, retriever: Any):
        self.retriever = retriever

    @property
    def total_chunks(self) -> int:
        return len(getattr(self.retriever, "chunks", []))

    def build_index(self, *, force: bool = False, incremental: bool = True) -> None:
        self.retriever.build_index(force=force, incremental=incremental)

    def search_gene_chunks(
        self,
        query: str,
        *,
        top_k: int = 20,
        use_hybrid: bool = True,
        rerank: bool = True,
        rerank_top_n: int = 50,
    ):
        return asyncio.run(
            self.asearch_gene_chunks(
                query,
                top_k=top_k,
                use_hybrid=use_hybrid,
                rerank=rerank,
                rerank_top_n=rerank_top_n,
            )
        )

    async def asearch_gene_chunks(
        self,
        query: str,
        *,
        top_k: int = 20,
        use_hybrid: bool = True,
        rerank: bool = True,
        rerank_top_n: int = 50,
    ):
        if use_hybrid and hasattr(self.retriever, "hybrid_search"):
            return await self.retriever.hybrid_search(
                query,
                top_k=top_k,
                rerank=rerank,
                rerank_top_n=rerank_top_n,
            )
        return await asyncio.to_thread(self.retriever.search, query, top_k)
