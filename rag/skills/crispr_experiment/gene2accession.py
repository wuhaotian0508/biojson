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
    "T. aestivum": "Triticum aestivum",
}

_GENUS_MAP = {
    "G.": "Glycine",
    "A.": "Arabidopsis",
    "O.": "Oryza",
    "Z.": "Zea",
    "N.": "Nicotiana",
    "T.": "Triticum",
}

# 基因名常见的物种缩写前缀 → 对应物种拉丁名
# 论文中常写 GmIFS2，但 NCBI Gene 数据库中注册名为 IFS2
_GENE_PREFIX_TO_SPECIES = {
    "Gm":  "Glycine max",
    "At":  "Arabidopsis thaliana",
    "Os":  "Oryza sativa",
    "Zm":  "Zea mays",
    "Nt":  "Nicotiana tabacum",
    "Nb":  "Nicotiana benthamiana",
    "Ta":  "Triticum aestivum",
    "Sl":  "Solanum lycopersicum",
    "St":  "Solanum tuberosum",
    "Md":  "Malus domestica",
    "Vv":  "Vitis vinifera",
    "Br":  "Brassica rapa",
    "Bn":  "Brassica napus",
    "Cs":  "Cucumis sativus",
    "Gh":  "Gossypium hirsutum",
    "Pv":  "Phaseolus vulgaris",
    "Lj":  "Lotus japonicus",
    "Mt":  "Medicago truncatula",
}


def _strip_species_prefix(gene_name: str) -> Optional[str]:
    """
    去除基因名中的物种缩写前缀，返回去掉前缀后的基因名。

    例如: "GmIFS2" → "IFS2", "AtMYB4" → "MYB4"
    如果基因名不以已知前缀开头或去掉后为空，则返回 None。
    """
    for prefix in sorted(_GENE_PREFIX_TO_SPECIES, key=len, reverse=True):
        if gene_name.startswith(prefix) and len(gene_name) > len(prefix):
            return gene_name[len(prefix):]
    return None


def _normalize_species_name(species: str) -> str:
    """
    将缩写形式的物种名标准化为完整拉丁双名（属名 + 种加词）。

    处理三种情况：
    1. 已在 _SPECIES_ABBREV_MAP 中的缩写（如 "G. max" → "Glycine max"）
    2. 已经是完整拉丁名（如 "Glycine max"）—— 原样返回
    3. "属名缩写. 种加词" 格式（如 "A. thaliana"）—— 通过 _GENUS_MAP 展开属名

    参数:
        species: 物种名字符串，可以是缩写或完整拉丁名

    返回:
        标准化后的完整拉丁名；如果无法识别则原样返回
    """
    if not species:
        return ""
    s = species.strip()                              # s: 去除首尾空白后的物种名

    # ---- 优先查固定映射表 ----
    if s in _SPECIES_ABBREV_MAP:
        return _SPECIES_ABBREV_MAP[s]

    # ---- 已是完整拉丁名（首字母大写 + 空格 + 全小写种加词）—— 直接返回 ----
    if re.match(r"^[A-Z][a-z]+ [a-z][a-zA-Z-]*$", s):
        return s

    # ---- 尝试展开 "X. epithet" 缩写格式 ----
    m = re.match(r"^([A-Z]\.)\s+([a-z][a-zA-Z-]*)$", s)
    if m:
        genus_abbrev, epithet = m.groups()   # genus_abbrev: 属名缩写如 "A."；epithet: 种加词如 "thaliana"
        genus = _GENUS_MAP.get(genus_abbrev) # genus: 完整属名，如 "Arabidopsis"；查不到则 None
        if genus:
            return f"{genus} {epithet}"

    return s   # 无法识别时原样返回


def _esearch_gene(gene_name: str, species: str, retmax: int = 10) -> List[str]:
    """
    执行单次 NCBI Gene esearch 查询，返回 Gene ID 列表。
    """
    query = f'"{gene_name}"[Gene Name]'
    if species:
        query += f' AND "{species}"[Organism]'

    with Entrez.esearch(db="gene", term=query, retmax=retmax) as handle:
        record = Entrez.read(handle)

    return record.get("IdList", [])


def _search_gene_ids(gene_name: str, species: str, retmax: int = 10) -> List[str]:
    """
    在 NCBI Gene 数据库中按基因名和物种搜索，返回 Gene ID 列表。

    搜索策略（依次尝试，有结果即返回）：
    1. 原始基因名精确搜索，如 "GmIFS2"[Gene Name] AND "Glycine max"[Organism]
    2. 去掉物种缩写前缀后搜索，如 "IFS2"[Gene Name] AND "Glycine max"[Organism]
       （NCBI Gene 中大多数植物基因不含物种前缀）
    3. 原始基因名作为自由文本搜索（不限定 [Gene Name] 字段）

    参数:
        gene_name: 基因名，如 "GmIFS2"
        species:   物种拉丁名，如 "Glycine max"；为空时仅按基因名搜索
        retmax:    最多返回的 Gene ID 数量，默认 10

    返回:
        NCBI Gene ID 字符串列表，如 ["733567", "100101456"]；无结果时为空列表
    """
    # ---- 策略1：原始基因名精确搜索 ----
    ids = _esearch_gene(gene_name, species, retmax)
    if ids:
        return ids

    # ---- 策略2：去掉物种缩写前缀后搜索 ----
    short_name = _strip_species_prefix(gene_name)
    if short_name:
        ids = _esearch_gene(short_name, species, retmax)
        if ids:
            return ids

    # ---- 策略3：原始基因名自由文本搜索 ----
    query = f'"{gene_name}"'
    if species:
        query += f' AND "{species}"[Organism]'
    with Entrez.esearch(db="gene", term=query, retmax=retmax) as handle:
        record = Entrez.read(handle)
    return record.get("IdList", [])


def _link_gene_to_nuccore(gene_id: str) -> List[str]:
    """
    通过 NCBI elink 查询 Gene → Nuccore 的关联关系，返回核酸记录 ID 列表。

    NCBI 的 elink 接口可以跨数据库查找关联记录，这里用于
    找到某个 Gene 对应的所有核酸序列记录（mRNA、基因组片段等）。

    参数:
        gene_id: NCBI Gene 数据库中的基因 ID（字符串形式），如 "733567"

    返回:
        Nuccore 数据库中的记录 ID 字符串列表；无关联时为空列表
    """
    with Entrez.elink(dbfrom="gene", db="nuccore", id=gene_id) as handle:
        record = Entrez.read(handle)   # record: elink 返回结果列表，第 0 项为本次查询结果

    nuccore_ids = []
    # record[0]["LinkSetDb"]: 包含所有关联数据库的链接集合，每项对应一类关联
    for linksetdb in record[0].get("LinkSetDb", []):
        # linksetdb["Link"]: 该类关联下的所有记录链接
        for link in linksetdb.get("Link", []):
            nuccore_ids.append(link["Id"])   # link["Id"]: Nuccore 记录的内部数字 ID

    return nuccore_ids


def _fetch_nuccore_summaries(nuccore_ids: List[str]) -> List[dict]:
    """
    批量获取 Nuccore 记录的摘要信息（accession 和标题）。

    使用 Entrez esummary 接口，一次性查询多个记录。

    参数:
        nuccore_ids: Nuccore 数据库内部 ID 列表（来自 elink 结果）

    返回:
        摘要字典列表，每项形如：
        {"accession": "NM_001248.3", "title": "Glycine max fatty acid desaturase 2 mRNA"}
    """
    if not nuccore_ids:
        return []

    with Entrez.esummary(db="nuccore", id=",".join(nuccore_ids)) as handle:
        summary = Entrez.read(handle)   # summary: esummary 返回的记录列表

    return [
        {
            # AccessionVersion: 带版本号的 accession，如 "NM_001248.3"
            "accession": item.get("AccessionVersion", ""),
            # Title: 记录标题，包含物种、基因功能等信息
            "title": item.get("Title", ""),
        }
        for item in summary
    ]


def _direct_nuccore_search(gene_name: str, species: str, retmax: int = 10) -> List[dict]:
    """
    回退方案：绕过 Gene 数据库，直接在 Nuccore 中按关键词搜索。

    当 Gene→Nuccore elink 未能找到结果时调用此函数。
    搜索条件比 Gene 数据库更宽松，可能匹配到更多记录（包括专利序列等），
    因此结果质量相对较低，仅作为兜底。

    参数:
        gene_name: 基因名关键词
        species:   物种拉丁名（用于缩小搜索范围）
        retmax:    最多返回的 Nuccore ID 数量

    返回:
        与 _fetch_nuccore_summaries() 相同格式的摘要列表
    """
    # query: 直接在 Nuccore 文本字段中搜索基因名 + 物种
    query = f'"{gene_name}"'
    if species:
        query += f' AND "{species}"[Organism]'

    with Entrez.esearch(db="nuccore", term=query, retmax=retmax) as handle:
        rec = Entrez.read(handle)   # rec: esearch 返回结果，包含 IdList

    ids = rec.get("IdList", [])    # ids: 匹配到的 Nuccore 内部 ID 列表
    if not ids:
        return []

    return _fetch_nuccore_summaries(ids)


def _pick_best_accession(records: List[dict], gene_name: str) -> str:
    """
    从候选 Nuccore 记录中选择最适合的 accession。

    选择优先级（从高到低）：
    1. 标题中含目标基因名 且 含 mRNA/cDNA/transcript 关键词的记录
    2. 标题中含目标基因名的记录（无转录本类型约束）
    3. 标题中含 mRNA/cDNA/transcript 关键词的记录（不含基因名）
    4. 第一条记录（兜底）

    优先选择 mRNA/cDNA 记录，是因为它们通常只含编码区序列，
    长度适中，适合 CRISPR 靶点设计（避免基因组序列中的内含子干扰）。

    参数:
        records:   候选摘要列表（来自 _fetch_nuccore_summaries）
        gene_name: 目标基因名，用于标题匹配

    返回:
        最佳 accession 字符串；无候选时返回空字符串
    """
    if not records:
        return ""

    gene_name_lower = gene_name.lower()   # 转小写便于不区分大小写比较

    # exact_gene: 标题中明确包含目标基因名的记录子集
    exact_gene = [r for r in records if gene_name_lower in r.get("title", "").lower()]

    if exact_gene:
        # transcript_like: 在含基因名的记录中进一步筛选 mRNA/cDNA 类型
        transcript_like = [
            r for r in exact_gene
            if any(k in r.get("title", "").lower() for k in ["mrna", "cdna", "transcript"])
        ]
        # 有转录本记录优先选第一个，否则选含基因名的第一个
        return (transcript_like[0] if transcript_like else exact_gene[0]).get("accession", "")

    # 没有含基因名的记录时，退而求其次选转录本类型记录
    transcript_like = [
        r for r in records
        if any(k in r.get("title", "").lower() for k in ["mrna", "cdna", "transcript"])
    ]
    if transcript_like:
        return transcript_like[0].get("accession", "")

    # 最后兜底：返回第一条记录的 accession
    return records[0].get("accession", "")


def _find_accession_for_gene(gene_name: str, species: str, pause: float = 0.34) -> str:
    """
    查询单个基因对应的最佳 NCBI accession。

    执行流程（两阶段查询）：
    1. 主路径：NCBI Gene → elink → Nuccore → 选最佳 accession
    2. 回退路径（主路径无结果）：直接 Nuccore 关键词搜索

    每次 NCBI API 调用后暂停 `pause` 秒，遵守 NCBI 速率限制
    （无 API Key 时每秒最多 3 次请求，即每次间隔 ≥ 0.34s）。

    参数:
        gene_name: 基因名，如 "GmFAD2"
        species:   物种名（可以是缩写，内部会自动标准化）
        pause:     每次 API 请求后的等待时间（秒），默认 0.34s

    返回:
        最佳 accession 字符串（如 "NM_001248.3"）；未找到时返回空字符串
    """
    # normalized_species: 标准化后的完整物种拉丁名，如 "Glycine max"
    normalized_species = _normalize_species_name(species)

    # ---- 阶段 1：通过 Gene 数据库查找 ----
    gene_ids = _search_gene_ids(gene_name, normalized_species)   # gene_ids: Gene ID 列表
    time.sleep(pause)

    all_records = []   # all_records: 收集所有关联的 Nuccore 摘要记录
    for gid in gene_ids:
        nuccore_ids = _link_gene_to_nuccore(gid)   # nuccore_ids: 该 Gene 关联的 Nuccore ID 列表
        time.sleep(pause)
        if nuccore_ids:
            summaries = _fetch_nuccore_summaries(nuccore_ids)
            all_records.extend(summaries)
            time.sleep(pause)

    accession = _pick_best_accession(all_records, gene_name)
    if accession:
        return accession

    # ---- 阶段 2：回退到直接 Nuccore 搜索 ----
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
