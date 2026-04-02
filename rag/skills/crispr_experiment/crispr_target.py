"""
Step 3: FASTA 序列 → CRISPR 靶点

功能：读取 FASTA 序列文件，提交到华中农大 CRISPR 设计网站，
     为每条序列筛选第一个落在 exon 区域的 CRISPR 靶点。

输入：fasta_file — Step 2 生成的 FASTA 文件
     work_dir — 工作目录（Path）
输出：CRISPR 靶点 TSV 文件路径（Path）
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def run_crispr_target(fasta_file: Path, work_dir: Path) -> Path:
    """
    设计 CRISPR 靶点。

    复用 分析流程/crispr_target.py 中的核心函数：
    - parse_fasta(): 解析 FASTA 文件
    - fetch_result_page(): 向 CRISPR 网站提交序列
    - extract_rows(): 从 HTML 结果中提取候选靶点
    - find_first_exon_row(): 筛选第一个 exon 区域靶点
    - build_output_row() / write_table(): 格式化输出

    参数:
        fasta_file: Step 2 生成的 FASTA 序列文件
        work_dir: 临时工作目录

    返回:
        CRISPR 靶点 TSV 文件路径（含 Seq_name, Sequence, PAM 等列）

    异常:
        ValueError: 当未能为任何序列获取到 exon 区靶点时抛出
    """
    # ---- 动态导入 分析流程 中的 CRISPR 靶点设计脚本 ----
    import importlib.util
    _PIPELINE_SCRIPTS_DIR = Path(__file__).parent.parent.parent / "分析流程"
    spec = importlib.util.spec_from_file_location(
        "crispr_target_mod", _PIPELINE_SCRIPTS_DIR / "crispr_target.py"
    )
    if spec is None or spec.loader is None:
        raise ImportError("无法加载 crispr_target.py 脚本")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # ---- 输出文件路径 ----
    target_file = work_dir / "crispr_target_recommended.txt"
    output_rows = []

    # ---- 逐条处理 FASTA 序列 ----
    for seq_name, sequence in mod.parse_fasta(fasta_file):
        try:
            # 提交序列到 CRISPR 网站获取 HTML 结果页
            html_text = mod.fetch_result_page(sequence)
            # 解析 HTML 中的候选靶点列表
            all_rows = mod.extract_rows(html_text)
            # 筛选第一个落在 exon 区域的靶点
            exon_row = mod.find_first_exon_row(all_rows)

            if exon_row is None:
                logger.warning("序列 %s 未找到 exon 区域的 CRISPR 靶点", seq_name)
                continue

            output_rows.append(mod.build_output_row(seq_name, exon_row))
        except Exception as e:
            logger.warning("序列 %s 的 CRISPR 靶点设计失败: %s", seq_name, e)

    # ---- 检查结果 ----
    if not output_rows:
        raise ValueError("未能为任何序列获取 CRISPR 靶点")

    # ---- 写入 TSV 文件 ----
    mod.write_table(target_file, output_rows, "\t")
    return target_file
