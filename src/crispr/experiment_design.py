from __future__ import annotations

import csv
from pathlib import Path

from crispr.sop_formatter import format_sop_to_markdown

_KNOWN_ORGANISMS = {"Oryza", "Zea", "Nicotiana", "Triticum", "Glycine", "Arabidopsis"}


def _template_dirs() -> list[Path]:
    package_dir = Path(__file__).parent
    return [package_dir / "templates"]


def _get_template_text(organism: str) -> str:
    organism = organism if organism in _KNOWN_ORGANISMS else "Universal_Plant"
    filename = f"SOP_{organism}_CRISPR_SpCas9_base.txt"
    for template_dir in _template_dirs():
        template_path = template_dir / filename
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")
    raise FileNotFoundError(f"CRISPR SOP template not found: {filename}")


def _gene_info_from_accessions(accession_file: Path | None) -> dict[str, tuple[str, str]]:
    info = {}
    if accession_file and accession_file.exists():
        with accession_file.open(encoding="utf-8") as file:
            for line in file:
                parts = line.strip().split("\t")
                if len(parts) >= 3:
                    gene, species, accession = parts[:3]
                    info[accession] = (gene, species.split(" ")[0] if species else "Universal_Plant")
    return info


def run_experiment_design(
    target_file: Path,
    work_dir: Path,
    accession_file: Path | None = None,
) -> dict[str, str]:
    gene_info = _gene_info_from_accessions(accession_file)
    sops: dict[str, str] = {}
    with target_file.open(encoding="utf-8") as file:
        for row in csv.DictReader(file, delimiter="\t"):
            accession = row["Seq_name"]
            matched_gene, matched_organism = gene_info.get(accession, (accession, "Universal_Plant"))
            text = _get_template_text(matched_organism)
            sequence_rc = row.get("Sequence_RC", "")
            replacements = {
                "_gene_accession_": accession,
                "_target_number_": row.get("Target_number", ""),
                "_sequence_rc_": sequence_rc,
                "_sequence_rt_": sequence_rc,
                "_sequence_": row.get("Sequence", ""),
                "_PAM_": row.get("PAM", ""),
            }
            for placeholder, value in replacements.items():
                text = text.replace(placeholder, value)
            markdown_text = format_sop_to_markdown(text)
            (work_dir / f"SOP_{matched_organism}_CRISPR_SpCas9_{matched_gene}.md").write_text(
                markdown_text,
                encoding="utf-8",
            )
            (work_dir / f"CRISPR_SpCas9_Gene_Editing_{accession}.txt").write_text(
                markdown_text,
                encoding="utf-8",
            )
            sops[accession] = markdown_text
    if not sops:
        raise ValueError("未能生成任何实验方案")
    return sops


__all__ = ["run_experiment_design"]
