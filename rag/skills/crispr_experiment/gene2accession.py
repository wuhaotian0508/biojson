"""
Step 1: 基因名 → NCBI Accession

功能：接收基因名+物种列表，通过 NCBI Entrez API 查询每个基因对应的
     nuccore accession（优先选择 mRNA/cDNA 记录）。

输入：genes — [{"gene": "GmFAD2", "species": "Glycine max"}, ...]
     work_dir — 工作目录（Path）
输出：accession 文件路径（Path），每行格式：gene\tspecies\taccession
"""
from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import List, Optional

from Bio import Entrez

logger = logging.getLogger(__name__)

# ---- NCBI Entrez 邮箱标识（NCBI 要求每个请求携带） ----
_ENTREZ_EMAIL = "biojson_rag@example.com"

# ----------------------------
# 物种名缩写映射
# ----------------------------
_SPECIES_ABBREV_MAP = {
    "G. max": "Glycine max",
    "A. thaliana": "Arabidopsis thaliana",
    "O. sativa": "Oryza sativa",
    "Z. mays": "Zea mays",
    "N. tabacum": "Nicotiana tabacum",
}

_GENUS_MAP = {
    "G.": "Glycine",
    "A.": "Arabidopsis",
    "O.": "Oryza",
    "Z.": "Zea",
    "N.": "Nicotiana",
}


def _normalize_species_name(species: str) -> str:
    """将缩写物种名（如 'G. max'）转为完整拉丁名（'Glycine max'）。"""
    if not species:
        return ""
    s = species.strip()
    if s in _SPECIES_ABBREV_MAP:
        return _SPECIES_ABBREV_MAP[s]
    if re.match(r"^[A-Z][a-z]+ [a-z][a-zA-Z-]*$", s):
        return s
    m = re.match(r"^([A-Z]\.)\s+([a-z][a-zA-Z-]*)$", s)
    if m:
        genus_abbrev, epithet = m.groups()
        genus = _GENUS_MAP.get(genus_abbrev)
        if genus:
            return f"{genus} {epithet}"
    return s


def _search_gene_ids(gene_name: str, species: str, retmax: int = 10) -> List[str]:
    """在 NCBI Gene 中搜索 gene ID。"""
    query = f'"{gene_name}"[Gene Name]'
    if species:
        query += f' AND "{species}"[Organism]'
    with Entrez.esearch(db="gene", term=query, retmax=retmax) as handle:
        record = Entrez.read(handle)
    return record.get("IdList", [])


def _link_gene_to_nuccore(gene_id: str) -> List[str]:
    """Gene → Nuccore 链接查询。"""
    with Entrez.elink(dbfrom="gene", db="nuccore", id=gene_id) as handle:
        record = Entrez.read(handle)
    nuccore_ids = []
    for linksetdb in record[0].get("LinkSetDb", []):
        for link in linksetdb.get("Link", []):
            nuccore_ids.append(link["Id"])
    return nuccore_ids


def _fetch_nuccore_summaries(nuccore_ids: List[str]) -> List[dict]:
    """获取 Nuccore 记录的 accession 和 title。"""
    if not nuccore_ids:
        return []
    with Entrez.esummary(db="nuccore", id=",".join(nuccore_ids)) as handle:
        summary = Entrez.read(handle)
    return [
        {"accession": item.get("AccessionVersion", ""), "title": item.get("Title", "")}
        for item in summary
    ]


def _direct_nuccore_search(gene_name: str, species: str, retmax: int = 10) -> List[dict]:
    """回退方案：直接在 Nuccore 中搜索。"""
    query = f'"{gene_name}"'
    if species:
        query += f' AND "{species}"[Organism]'
    with Entrez.esearch(db="nuccore", term=query, retmax=retmax) as handle:
        rec = Entrez.read(handle)
    ids = rec.get("IdList", [])
    if not ids:
        return []
    return _fetch_nuccore_summaries(ids)


def _pick_best_accession(records: List[dict], gene_name: str) -> str:
    """从候选记录中选择最佳 accession。优先选含基因名的 mRNA/cDNA 记录。"""
    if not records:
        return ""
    gene_name_lower = gene_name.lower()
    exact_gene = [r for r in records if gene_name_lower in r.get("title", "").lower()]
    if exact_gene:
        transcript_like = [
            r for r in exact_gene
            if any(k in r.get("title", "").lower() for k in ["mrna", "cdna", "transcript"])
        ]
        return (transcript_like[0] if transcript_like else exact_gene[0]).get("accession", "")
    transcript_like = [
        r for r in records
        if any(k in r.get("title", "").lower() for k in ["mrna", "cdna", "transcript"])
    ]
    if transcript_like:
        return transcript_like[0].get("accession", "")
    return records[0].get("accession", "")


def _find_accession_for_gene(gene_name: str, species: str, pause: float = 0.34) -> str:
    """查询单个基因的 accession：Gene→Nuccore 链接，失败则直接 Nuccore 搜索。"""
    normalized_species = _normalize_species_name(species)

    gene_ids = _search_gene_ids(gene_name, normalized_species)
    time.sleep(pause)

    all_records = []
    for gid in gene_ids:
        nuccore_ids = _link_gene_to_nuccore(gid)
        time.sleep(pause)
        if nuccore_ids:
            summaries = _fetch_nuccore_summaries(nuccore_ids)
            all_records.extend(summaries)
            time.sleep(pause)

    accession = _pick_best_accession(all_records, gene_name)
    if accession:
        return accession

    direct_records = _direct_nuccore_search(gene_name, normalized_species)
    time.sleep(pause)
    return _pick_best_accession(direct_records, gene_name)


# ------------------------------------------------------------------
# 公开接口
# ------------------------------------------------------------------

def run_gene2accession(genes: list[dict], work_dir: Path) -> Path:
    """
    批量查询 NCBI accession。

    参数:
        genes: 基因列表，每项包含 "gene"（基因名）和 "species"（拉丁名）
        work_dir: 临时工作目录

    返回:
        accession 文件路径（3 列 TSV：gene, species, accession）

    异常:
        ValueError: 当所有基因都未能找到 accession 时抛出
    """
    Entrez.email = _ENTREZ_EMAIL

    gene_file = work_dir / "gene_to_edit.txt"
    acc_file = work_dir / "accession.txt"

    with open(gene_file, "w", encoding="utf-8") as f:
        for g in genes:
            f.write(f"{g['gene']}\t{g['species']}\n")

    results = []
    for g in genes:
        try:
            acc = _find_accession_for_gene(g["gene"], g["species"])
        except Exception as e:
            logger.warning("基因 %s 的 accession 查询失败: %s", g["gene"], e)
            acc = ""
        results.append((g["gene"], g["species"], acc))

    with open(acc_file, "w", encoding="utf-8") as f:
        for gene, species, acc in results:
            f.write(f"{gene}\t{species}\t{acc}\n")

    if not any(r[2] for r in results):
        raise ValueError("未能为任何基因找到 NCBI accession")

    return acc_file
