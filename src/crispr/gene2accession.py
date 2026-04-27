from __future__ import annotations

import logging
import re
import time
from pathlib import Path

from Bio import Entrez

logger = logging.getLogger(__name__)

_ENTREZ_EMAIL = "nutrimaster_rag@example.com"
_SPECIES_ABBREV_MAP = {
    "G. max": "Glycine max",
    "A. thaliana": "Arabidopsis thaliana",
    "O. sativa": "Oryza sativa",
    "Z. mays": "Zea mays",
    "N. tabacum": "Nicotiana tabacum",
    "T. aestivum": "Triticum aestivum",
}
_GENUS_MAP = {"G.": "Glycine", "A.": "Arabidopsis", "O.": "Oryza", "Z.": "Zea", "N.": "Nicotiana", "T.": "Triticum"}
_GENE_PREFIX_TO_SPECIES = {
    "Gm": "Glycine max",
    "At": "Arabidopsis thaliana",
    "Os": "Oryza sativa",
    "Zm": "Zea mays",
    "Nt": "Nicotiana tabacum",
    "Nb": "Nicotiana benthamiana",
    "Ta": "Triticum aestivum",
    "Sl": "Solanum lycopersicum",
    "St": "Solanum tuberosum",
    "Md": "Malus domestica",
    "Vv": "Vitis vinifera",
    "Br": "Brassica rapa",
    "Bn": "Brassica napus",
    "Cs": "Cucumis sativus",
    "Gh": "Gossypium hirsutum",
    "Pv": "Phaseolus vulgaris",
    "Lj": "Lotus japonicus",
    "Mt": "Medicago truncatula",
}


def _strip_species_prefix(gene_name: str) -> str | None:
    for prefix in sorted(_GENE_PREFIX_TO_SPECIES, key=len, reverse=True):
        if gene_name.startswith(prefix) and len(gene_name) > len(prefix):
            return gene_name[len(prefix):]
    return None


def _normalize_species_name(species: str) -> str:
    if not species:
        return ""
    species = species.strip()
    if species in _SPECIES_ABBREV_MAP:
        return _SPECIES_ABBREV_MAP[species]
    if re.match(r"^[A-Z][a-z]+ [a-z][a-zA-Z-]*$", species):
        return species
    if match := re.match(r"^([A-Z]\.)\s+([a-z][a-zA-Z-]*)$", species):
        genus = _GENUS_MAP.get(match.group(1))
        if genus:
            return f"{genus} {match.group(2)}"
    return species


def _esearch_gene(gene_name: str, species: str, retmax: int = 10) -> list[str]:
    query = f'"{gene_name}"[Gene Name]'
    if species:
        query += f' AND "{species}"[Organism]'
    with Entrez.esearch(db="gene", term=query, retmax=retmax) as handle:
        record = Entrez.read(handle)
    return record.get("IdList", [])


def _search_gene_ids(gene_name: str, species: str, retmax: int = 10) -> list[str]:
    ids = _esearch_gene(gene_name, species, retmax)
    if ids:
        return ids
    if short_name := _strip_species_prefix(gene_name):
        ids = _esearch_gene(short_name, species, retmax)
        if ids:
            return ids
    query = f'"{gene_name}"'
    if species:
        query += f' AND "{species}"[Organism]'
    with Entrez.esearch(db="gene", term=query, retmax=retmax) as handle:
        return Entrez.read(handle).get("IdList", [])


def _link_gene_to_nuccore(gene_id: str) -> list[str]:
    with Entrez.elink(dbfrom="gene", db="nuccore", id=gene_id) as handle:
        record = Entrez.read(handle)
    return [
        link["Id"]
        for linksetdb in record[0].get("LinkSetDb", [])
        for link in linksetdb.get("Link", [])
    ]


def _fetch_nuccore_summaries(nuccore_ids: list[str]) -> list[dict]:
    if not nuccore_ids:
        return []
    with Entrez.esummary(db="nuccore", id=",".join(nuccore_ids)) as handle:
        summary = Entrez.read(handle)
    return [{"accession": item.get("AccessionVersion", ""), "title": item.get("Title", "")} for item in summary]


def _direct_nuccore_search(gene_name: str, species: str, retmax: int = 10) -> list[dict]:
    query = f'"{gene_name}"'
    if species:
        query += f' AND "{species}"[Organism]'
    with Entrez.esearch(db="nuccore", term=query, retmax=retmax) as handle:
        ids = Entrez.read(handle).get("IdList", [])
    return _fetch_nuccore_summaries(ids)


def _pick_best_accession(records: list[dict], gene_name: str) -> str:
    if not records:
        return ""
    gene_name_lower = gene_name.lower()
    exact_gene = [record for record in records if gene_name_lower in record.get("title", "").lower()]
    if exact_gene:
        transcript_like = [
            record
            for record in exact_gene
            if any(key in record.get("title", "").lower() for key in ("mrna", "cdna", "transcript"))
        ]
        return (transcript_like[0] if transcript_like else exact_gene[0]).get("accession", "")
    transcript_like = [
        record
        for record in records
        if any(key in record.get("title", "").lower() for key in ("mrna", "cdna", "transcript"))
    ]
    return (transcript_like[0] if transcript_like else records[0]).get("accession", "")


def _find_accession_for_gene(gene_name: str, species: str, pause: float = 0.34) -> str:
    normalized_species = _normalize_species_name(species)
    gene_ids = _search_gene_ids(gene_name, normalized_species)
    time.sleep(pause)
    records = []
    for gene_id in gene_ids:
        nuccore_ids = _link_gene_to_nuccore(gene_id)
        time.sleep(pause)
        if nuccore_ids:
            records.extend(_fetch_nuccore_summaries(nuccore_ids))
            time.sleep(pause)
    accession = _pick_best_accession(records, gene_name)
    if accession:
        return accession
    direct_records = _direct_nuccore_search(gene_name, normalized_species)
    time.sleep(pause)
    return _pick_best_accession(direct_records, gene_name)


def run_gene2accession(genes: list[dict], work_dir: Path) -> Path:
    Entrez.email = _ENTREZ_EMAIL
    acc_file = work_dir / "accession.txt"
    results = []
    for gene in genes:
        try:
            accession = _find_accession_for_gene(gene["gene"], gene["species"])
        except Exception as exc:
            logger.warning("Gene %s accession lookup failed: %s", gene["gene"], exc)
            accession = ""
        results.append((gene["gene"], gene["species"], accession))
    with acc_file.open("w", encoding="utf-8") as file:
        for gene_name, species, accession in results:
            file.write(f"{gene_name}\t{species}\t{accession}\n")
    if not any(result[2] for result in results):
        raise ValueError("未能为任何基因找到 NCBI accession")
    return acc_file


__all__ = [
    "_normalize_species_name",
    "_search_gene_ids",
    "run_gene2accession",
]
