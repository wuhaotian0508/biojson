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
from pathlib import Path

from Bio import Entrez

logger = logging.getLogger(__name__)

# ---- NCBI Entrez 邮箱标识（NCBI 要求每个请求携带） ----
_ENTREZ_EMAIL = "biojson_rag@example.com"


def run_gene2accession(genes: list[dict], work_dir: Path) -> Path:
    """
    批量查询 NCBI accession。

    对于每个基因，调用 分析流程/gene2accession.py.py 中的
    find_accession_for_gene() 执行 Gene → Nuccore 链接查询。
    若链接查询失败，会自动回退到 Nuccore 直接检索。

    参数:
        genes: 基因列表，每项包含 "gene"（基因名）和 "species"（拉丁名）
        work_dir: 临时工作目录，用于存放中间文件

    返回:
        accession 文件路径（3 列 TSV：gene, species, accession）

    异常:
        ValueError: 当所有基因都未能找到 accession 时抛出
    """
    # ---- 动态导入 分析流程 中的核心查找函数 ----
    import importlib.util
    _PIPELINE_SCRIPTS_DIR = Path(__file__).parent.parent.parent / "分析流程"
    script_path = _PIPELINE_SCRIPTS_DIR / "gene2accession.py.py"
    if not script_path.exists():
        raise FileNotFoundError(
            f"SOP 依赖脚本缺失: {script_path}. 当前仓库中未找到旧版分析流程目录。"
        )
    spec = importlib.util.spec_from_file_location(
        "gene2accession_py", script_path
    )
    if spec is None or spec.loader is None:
        raise ImportError("无法加载 gene2accession.py.py 脚本")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # ---- 设置 Entrez 邮箱 ----
    Entrez.email = _ENTREZ_EMAIL

    # ---- 写入基因列表文件（用于记录/调试） ----
    gene_file = work_dir / "gene_to_edit.txt"
    acc_file = work_dir / "accession.txt"

    with open(gene_file, "w", encoding="utf-8") as f:
        for g in genes:
            f.write(f"{g['gene']}\t{g['species']}\n")

    # ---- 逐个查询 accession ----
    results = []
    for g in genes:
        try:
            # find_accession_for_gene: 先 Gene→Nuccore 链接，失败则直接 Nuccore 搜索
            acc = mod.find_accession_for_gene(g["gene"], g["species"])
        except Exception as e:
            logger.warning("基因 %s 的 accession 查询失败: %s", g["gene"], e)
            acc = ""
        results.append((g["gene"], g["species"], acc))

    # ---- 写入结果文件 ----
    with open(acc_file, "w", encoding="utf-8") as f:
        for gene, species, acc in results:
            f.write(f"{gene}\t{species}\t{acc}\n")

    # ---- 检查是否至少有一个有效 accession ----
    if not any(r[2] for r in results):
        raise ValueError("未能为任何基因找到 NCBI accession")

    return acc_file
