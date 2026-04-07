#!/usr/bin/env python3

import argparse
import csv
import re
import sys
import time
from typing import Optional, List

from Bio import Entrez

# 这个脚本的作用：
# 1. 读取用户提供的“基因名 + 物种名”表格；
# 2. 先到 NCBI Gene 检索候选 gene 记录；
# 3. 再从 Gene 记录跳转到 NCBI Nuccore（核酸序列库）；
# 4. 从候选核酸记录中挑出最合适的 accession；
# 5. 把 accession 追加到原始表格中输出。
#
# 它不做 LLM 推理，也不从论文文本里抽取基因，
# 只是把“已经给定的基因名”映射成 accession。

# ----------------------------
# User-configurable species map
# ----------------------------
SPECIES_ABBREV_MAP = {
    "G. max": "Glycine max",
    "A. thaliana": "Arabidopsis thaliana",
    "O. sativa": "Oryza sativa",
    "Z. mays": "Zea mays",
    "N. tabacum": "Nicotiana tabacum",
    "T. aestivum": "Triticum aestivum",
}

# Optional genus fallback for patterns like "G. max"
GENUS_MAP = {
    "G.": "Glycine",
    "A.": "Arabidopsis",
    "O.": "Oryza",
    "Z.": "Zea",
    "N.": "Nicotiana",
    "T.": "Triticum",
}


def normalize_species_name(species: str) -> str:
    """
    Convert abbreviated species names like 'G. max' to 'Glycine max'.
    If already a full binomial name, return unchanged.

    功能说明：
    - 输入可能是缩写物种名，例如 “G. max”；
    - 这个函数会尽量把它标准化为 NCBI 更容易识别的全名，例如 “Glycine max”；
    - 如果本来就是标准双名法（Genus species），则直接返回；
    - 如果无法识别，就保留原始输入，交给后续 NCBI 查询去处理。

    为什么需要它：
    - NCBI 检索对物种名比较敏感；
    - 用户输入的物种名格式可能不统一，所以先做一次轻量规范化。
    """
    if not species:
        return ""

    s = species.strip()

    if s in SPECIES_ABBREV_MAP:
        return SPECIES_ABBREV_MAP[s]

    # Already looks like "Genus species"
    if re.match(r"^[A-Z][a-z]+ [a-z][a-zA-Z-]*$", s):
        return s

    # Try expanding patterns like "G. max"
    m = re.match(r"^([A-Z]\.)\s+([a-z][a-zA-Z-]*)$", s)
    if m:
        genus_abbrev, epithet = m.groups()
        genus = GENUS_MAP.get(genus_abbrev)
        if genus:
            return f"{genus} {epithet}"

    return s


def search_gene_ids(gene_name: str, species: str, retmax: int = 10) -> List[str]:
    """
    Search NCBI Gene for gene IDs using gene name + organism.

    功能说明：
    - 在 NCBI Gene 数据库中检索某个基因名；
    - 如果提供了物种名，则同时限定 Organism 字段，减少误匹配；
    - 返回的是 Gene 数据库中的 ID 列表，而不是 accession。

    输入：
    - gene_name: 目标基因名，例如 GmMYB4
    - species: 物种名，例如 Glycine max
    - retmax: 最多返回多少条候选记录

    输出：
    - 一个 Gene ID 列表，例如 ["12345", "67890"]

    说明：
    - 这里只是第一步粗检索，后面还需要继续把 Gene 记录映射到 Nuccore 记录。
    """
    query = f'"{gene_name}"[Gene Name]'
    if species:
        query += f' AND "{species}"[Organism]'

    with Entrez.esearch(db="gene", term=query, retmax=retmax) as handle:
        record = Entrez.read(handle)

    return record.get("IdList", [])


def link_gene_to_nuccore(gene_id: str) -> List[str]:
    """
    Follow Gene -> Nuccore links.

    功能说明：
    - 给定一个 NCBI Gene ID，去查询这个基因关联的核酸序列记录；
    - 这些核酸序列记录位于 Nuccore 数据库中；
    - 返回的是 Nuccore ID 列表。

    为什么要这样做：
    - Gene 数据库存的是“基因实体”；
    - 真正下载序列通常要去 Nuccore；
    - 所以这个函数负责完成 Gene -> Nuccore 的跳转。
    """
    with Entrez.elink(dbfrom="gene", db="nuccore", id=gene_id) as handle:
        record = Entrez.read(handle)

    nuccore_ids = []
    for linksetdb in record[0].get("LinkSetDb", []):
        for link in linksetdb.get("Link", []):
            nuccore_ids.append(link["Id"])

    return nuccore_ids


def fetch_nuccore_summaries(nuccore_ids: List[str]) -> List[dict]:
    """
    Fetch accession/version and title for Nuccore records.

    功能说明：
    - 对一批 Nuccore ID 查询摘要信息；
    - 重点取两个字段：
      1. accession/version（后续要真正使用的 accession）
      2. title（用于判断哪个记录更像目标转录本）

    输出格式：
    - 返回字典列表，例如：
      [{"accession": "NM_xxx", "title": "..."}, ...]

    为什么不直接下载序列：
    - 因为一个基因可能对应多个序列候选；
    - 先看标题再做筛选，可以提高选中正确 accession 的概率。
    """
    if not nuccore_ids:
        return []

    with Entrez.esummary(db="nuccore", id=",".join(nuccore_ids)) as handle:
        summary = Entrez.read(handle)

    results = []
    for item in summary:
        results.append({
            "accession": item.get("AccessionVersion", ""),
            "title": item.get("Title", ""),
        })
    return results


def direct_nuccore_search(gene_name: str, species: str, retmax: int = 10) -> List[dict]:
    """
    Fallback direct search in nuccore if gene->nuccore linking fails.

    功能说明：
    - 当“先查 Gene 再跳 Nuccore”的主路径没有找到合适结果时，
      直接在 Nuccore 里用 gene_name + species 检索；
    - 这是一个兜底策略（fallback）。

    返回：
    - 与 fetch_nuccore_summaries 一致的记录列表，便于后续复用同一套筛选逻辑。

    设计原因：
    - 某些基因在 Gene 和 Nuccore 之间链接不完整；
    - 直接检索 Nuccore 有时反而能搜到可用记录。
    """
    query = f'"{gene_name}"'
    if species:
        query += f' AND "{species}"[Organism]'

    with Entrez.esearch(db="nuccore", term=query, retmax=retmax) as handle:
        rec = Entrez.read(handle)

    ids = rec.get("IdList", [])
    if not ids:
        return []

    return fetch_nuccore_summaries(ids)


def pick_best_accession(records: List[dict], gene_name: str) -> str:
    """
    Pick the best accession from candidate nuccore records.
    Preference:
      1. title containing the exact gene name
      2. titles mentioning mRNA/cDNA/transcript
      3. otherwise first record

    功能说明：
    - 一个基因经常会对应多条候选 Nuccore 记录；
    - 这个函数根据标题内容，从候选中挑出“最像目标记录”的 accession。

    选择策略：
    1. 优先选 title 中明确包含 gene_name 的记录；
    2. 在这些记录里，再优先选带有 mRNA / cDNA / transcript 关键词的记录；
    3. 如果没有命中 gene_name，则退而求其次，选带 transcript 特征的记录；
    4. 再不行就取第一条。

    注意：
    - 这是一套启发式规则，不保证 100% 正确；
    - 但对于批量自动化流程来说，通常够用。
    """
    if not records:
        return ""

    gene_name_lower = gene_name.lower()

    exact_gene = [
        r for r in records
        if gene_name_lower in r.get("title", "").lower()
    ]
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


def find_accession_for_gene(gene_name: str, species: str, pause: float = 0.34) -> str:
    """
    Main lookup logic:
      1. Search Gene
      2. Link Gene -> Nuccore
      3. Pick best accession
      4. Fallback to direct nuccore search

    功能说明：
    - 这是 accession 查询的核心总控函数；
    - 它把前面的几个小函数串起来，形成完整查询流程。

    执行步骤：
    1. 先标准化物种名；
    2. 在 NCBI Gene 中搜索 gene ID；
    3. 对每个 gene ID，跳转到 Nuccore 获取候选核酸记录；
    4. 汇总候选记录并选择最优 accession；
    5. 如果主路径失败，则直接搜索 Nuccore 作为兜底。

    pause 参数说明：
    - 在多次网络请求之间 sleep 一小段时间；
    - 这是为了避免请求过快，对 NCBI 更友好。
    """
    normalized_species = normalize_species_name(species)

    # First try Gene -> Nuccore
    gene_ids = search_gene_ids(gene_name, normalized_species)
    time.sleep(pause)

    all_records = []
    for gid in gene_ids:
        nuccore_ids = link_gene_to_nuccore(gid)
        time.sleep(pause)

        if nuccore_ids:
            summaries = fetch_nuccore_summaries(nuccore_ids)
            all_records.extend(summaries)
            time.sleep(pause)

    accession = pick_best_accession(all_records, gene_name)
    if accession:
        return accession

    # Fallback: direct nuccore search
    direct_records = direct_nuccore_search(gene_name, normalized_species)
    time.sleep(pause)

    return pick_best_accession(direct_records, gene_name)


def process_table(
    input_file: str,
    output_file: str,
    delimiter: str,
    has_header: bool
) -> None:
    """
    Read 2-column table and write 3-column output:
      gene_name, species_name, accession

    功能说明：
    - 批量处理输入表格中的每一行；
    - 输入至少包含两列：基因名、物种名；
    - 输出是在原有列后面追加 accession 列。

    细节：
    - 支持是否带表头；
    - 对空行、列数不足、查询失败等情况做了容错；
    - 每行单独处理，某一行失败不会中断整个批处理。

    为什么这个函数重要：
    - 它是脚本的“批量入口”；
    - 真正把前面的单基因查询逻辑应用到整张表上。
    """
    with open(input_file, "r", newline="", encoding="utf-8") as infile, \
         open(output_file, "w", newline="", encoding="utf-8") as outfile:

        reader = csv.reader(infile, delimiter=delimiter)
        writer = csv.writer(outfile, delimiter=delimiter)

        first_row = True
        for row_num, row in enumerate(reader, start=1):
            if not row:
                writer.writerow(row + [""])
                continue

            if len(row) < 2:
                print(f"Warning: row {row_num} has fewer than 2 columns; leaving accession blank.", file=sys.stderr)
                writer.writerow(row + [""])
                continue

            gene_name = row[0].strip()
            species_name = row[1].strip()

            if first_row and has_header:
                writer.writerow(row + ["accession"])
                first_row = False
                continue

            first_row = False

            accession = ""
            try:
                if gene_name and species_name:
                    accession = find_accession_for_gene(gene_name, species_name)
            except Exception as e:
                print(
                    f"Warning: lookup failed for row {row_num} "
                    f"(gene='{gene_name}', species='{species_name}'): {e}",
                    file=sys.stderr
                )

            if accession:
                writer.writerow(row + [accession])
                print(f"Processed row {row_num}: gene: '{gene_name}', species: '{species_name}', accession found: '{accession}'")
            else:
                print(f"Processed row {row_num}: gene: '{gene_name}', species: '{species_name}', accession not found")
        print(f"Output file: {output_file}")


def parse_args():
    """
    解析命令行参数。

    支持的参数包括：
    - 输入文件、输出文件；
    - NCBI 所需 email / api-key；
    - 分隔符；
    - 输入是否带表头。

    这是命令行脚本的标准入口配置函数。
    """
    parser = argparse.ArgumentParser(
        description=(
            "Read a two-column table of gene names and species names, "
            "search NCBI Nucleotide, and write a new table with a third "
            "column containing the accession number."
        )
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Input 2-column table file"
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output file with appended accession column"
    )
    parser.add_argument(
        "--email",
        default="my_email@example.com",
        help="Email address for NCBI Entrez"
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Optional NCBI API key"
    )
    parser.add_argument(
        "--delimiter",
        default="\t",
        help=r"Input/output delimiter. Default is tab. Use ',' for CSV."
    )
    parser.add_argument(
        "--header",
        action="store_true",
        help="Indicate that the input file has a header row"
    )
    return parser.parse_args()


def main():
    """
    主函数。

    运行顺序：
    1. 解析命令行参数；
    2. 配置 Entrez.email 和可选 api_key；
    3. 调用 process_table 批量处理输入文件。

    这是 gene2accession.py 的实际执行入口。
    """
    args = parse_args()

    Entrez.email = args.email
    if args.api_key:
        Entrez.api_key = args.api_key

    process_table(
        input_file=args.input,
        output_file=args.output,
        delimiter=args.delimiter,
        has_header=args.header
    )


if __name__ == "__main__":
    main()