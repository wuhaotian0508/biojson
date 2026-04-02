"""
Step 4: CRISPR 靶点 → 实验方案 SOP

功能：读取 CRISPR 靶点 TSV 文件，将靶点信息填入 SOP 模板，
     为每个基因生成一份完整的 CRISPR-SpCas9 基因编辑实验方案。

输入：target_file — Step 3 生成的 CRISPR 靶点 TSV 文件
输出：sops 字典 {accession: sop_text}
"""
from __future__ import annotations

import csv
from pathlib import Path

# ---- SOP 模板文件路径（与本文件同目录） ----
_BASE_TEMPLATE_PATH = Path(__file__).parent / "CRISPR_SpCas9_Gene_Editing_base.txt"


def run_experiment_design(target_file: Path, work_dir: Path) -> dict[str, str]:
    """
    基于 CRISPR 靶点生成实验方案 SOP。

    读取靶点文件中的每一行（每行对应一个基因/accession），
    将靶点序列、PAM 等信息填入 SOP 模板中的占位符，
    生成完整的 CRISPR-SpCas9 实验方案文档。

    模板占位符说明：
    - _gene_accession_ / _gene_name_  → accession 编号
    - _target_number_                 → 靶点编号
    - _sequence_                      → 正向靶点序列 (20bp)
    - _sequence_rt_ / _sequence_rc_   → 反向互补序列
    - _PAM_                           → PAM 序列 (如 NGG)

    参数:
        target_file: Step 3 输出的 CRISPR 靶点 TSV 文件
        work_dir: 临时工作目录（用于保存生成的 SOP 文件）

    返回:
        字典 {accession: sop_text}，每个 accession 对应一份完整 SOP 文本

    异常:
        ValueError: 当未能生成任何实验方案时抛出
    """
    # ---- 读取 SOP 模板 ----
    base_text = _BASE_TEMPLATE_PATH.read_text(encoding="utf-8")
    sops = {}

    # ---- 逐行处理靶点数据 ----
    with open(target_file, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            accession = row["Seq_name"]
            text = base_text

            # ---- 替换模板中的占位符 ----
            replacements = [
                ("_gene_accession_", accession),
                ("_target_number_", row.get("Target_number", "")),
                ("_sequence_rt_", row.get("Sequence_RC", "")),
                ("_sequence_rc_", row.get("Sequence_RC", "")),
                ("_sequence_", row.get("Sequence", "")),
                ("_PAM_", row.get("PAM", "")),
                ("_gene_name_", accession),
            ]
            for placeholder, value in replacements:
                text = text.replace(placeholder, value)

            # ---- 保存单个 SOP 文件（便于下载/调试） ----
            output_path = work_dir / f"CRISPR_SpCas9_Gene_Editing_{accession}.txt"
            output_path.write_text(text, encoding="utf-8")
            sops[accession] = text

    # ---- 检查结果 ----
    if not sops:
        raise ValueError("未能生成任何实验方案")

    return sops
