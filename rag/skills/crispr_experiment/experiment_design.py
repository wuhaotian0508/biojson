"""
Step 4: CRISPR 靶点 → 实验方案 SOP

功能：读取 accession 文件获取基因名和物种信息，
     读取 CRISPR 靶点 TSV 文件获取靶点数据，
     按物种选择对应的 SOP 模板，填入靶点信息生成实验方案。

输入：target_file    — Step 3 生成的 CRISPR 靶点 TSV 文件
     accession_file — Step 1 生成的 accession TSV 文件（含物种信息）
输出：sops 字典 {accession: sop_text}
"""
from __future__ import annotations

import csv
from pathlib import Path

from .sop_formatter import format_sop_to_markdown

# ---- SOP 模板目录（与本文件同目录） ----
_TEMPLATE_DIR = Path(__file__).parent

# ---- 支持的物种属名列表（对应 SOP 模板文件名中的物种部分） ----
_KNOWN_ORGANISMS = ['Oryza', 'Zea', 'Nicotiana', 'Triticum', 'Glycine', 'Arabidopsis']


def _get_template_text(organism: str) -> str:
    """
    根据物种属名加载对应的 SOP 模板文本。

    模板命名规则：SOP_{organism}_CRISPR_SpCas9_base.txt
    未识别的物种回退到 Universal_Plant 通用模板。

    参数:
        organism: 物种属名，如 "Glycine"

    返回:
        SOP 模板文本
    """
    if organism not in _KNOWN_ORGANISMS:
        organism = 'Universal_Plant'

    template_path = _TEMPLATE_DIR / f"SOP_{organism}_CRISPR_SpCas9_base.txt"
    return template_path.read_text(encoding="utf-8")


def run_experiment_design(target_file: Path, work_dir: Path, accession_file: Path | None = None) -> dict[str, str]:
    """
    基于 CRISPR 靶点生成实验方案 SOP。

    根据 accession 文件中的物种信息选择对应的 SOP 模板，
    再将靶点序列、PAM 等信息填入模板中的占位符，
    为每个基因生成一份完整的 CRISPR-SpCas9 实验方案。

    参数:
        target_file:    Step 3 输出的 CRISPR 靶点 TSV 文件
        work_dir:       临时工作目录
        accession_file: Step 1 输出的 accession TSV 文件（含物种列）。
                        如果为 None，则使用通用模板。

    返回:
        字典 {accession: sop_text}

    异常:
        ValueError: 当未能生成任何实验方案时抛出
    """
    # ---- 从 accession 文件中构建 gene_name → organism 映射 ----
    gene_info = {}  # {gene_name: organism_genus}
    if accession_file and accession_file.exists():
        with open(accession_file, encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    gene_name = parts[0]
                    # 从 "Glycine max" 提取属名 "Glycine"
                    organism = parts[1].split(' ')[0]
                    gene_info[gene_name] = organism

    sops = {}

    # ---- 逐行处理靶点数据 ----
    with open(target_file, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            accession = row["Seq_name"]

            # ---- 找到该 accession 对应的基因名和物种 ----
            # 在 accession 文件中查找哪个基因对应此 accession
            matched_gene = None
            matched_organism = 'Universal_Plant'
            if accession_file and accession_file.exists():
                with open(accession_file, encoding="utf-8") as af:
                    for line in af:
                        parts = line.strip().split('\t')
                        if len(parts) >= 3 and parts[2] == accession:
                            matched_gene = parts[0]
                            matched_organism = parts[1].split(' ')[0]
                            break

            # ---- 加载物种特定的 SOP 模板 ----
            text = _get_template_text(matched_organism)

            # ---- 替换模板中的占位符 ----
            text = text.replace('_gene_accession_', accession)
            text = text.replace('_target_number_', row.get("Target_number", ""))
            text = text.replace('_sequence_rc_', row.get("Sequence_RC", ""))
            text = text.replace('_sequence_', row.get("Sequence", ""))
            text = text.replace('_PAM_', row.get("PAM", ""))

            # ---- 转为 Markdown 格式 ----
            markdown_text = format_sop_to_markdown(text)

            # ---- 保存单个 SOP 文件（markdown 格式） ----
            gene_label = matched_gene or accession
            output_path = work_dir / f"SOP_{matched_organism}_CRISPR_SpCas9_{gene_label}.md"
            output_path.write_text(markdown_text, encoding="utf-8")
            sops[accession] = markdown_text

    if not sops:
        raise ValueError("未能生成任何实验方案")

    return sops
