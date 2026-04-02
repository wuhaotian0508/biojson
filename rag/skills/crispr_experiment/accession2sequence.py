"""
Step 2: Accession → FASTA 序列

功能：读取 accession 文件，从 NCBI Entrez efetch 下载对应的 FASTA 核酸序列。

输入：accession_file — Step 1 生成的 TSV 文件（3 列：gene, species, accession）
     work_dir — 工作目录（Path）
输出：FASTA 文件路径（Path）
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# ---- NCBI Entrez efetch 接口地址 ----
_ENTREZ_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
# ---- 请求标识 ----
_ENTREZ_EMAIL = "biojson_rag@example.com"


def run_accession2sequence(accession_file: Path, work_dir: Path) -> Path:
    """
    从 NCBI 下载基因序列。

    逐行读取 accession 文件，对每个有效 accession 调用 NCBI efetch
    下载 FASTA 格式序列，合并写入一个 FASTA 文件。
    每次请求间隔 0.34 秒以遵守 NCBI 速率限制。

    参数:
        accession_file: Step 1 生成的 accession TSV 文件
        work_dir: 临时工作目录

    返回:
        FASTA 文件路径

    异常:
        ValueError: 当没有有效 accession 可供下载，或未能下载到任何序列时抛出
    """
    fasta_file = work_dir / "sequence.fas"

    # ---- 从 accession 文件中提取有效 accession ----
    accessions = []
    with open(accession_file, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            # 第 3 列为 accession，跳过空值
            if len(parts) >= 3 and parts[2]:
                accessions.append(parts[2])

    if not accessions:
        raise ValueError("没有有效的 accession 可供下载序列")

    # ---- 逐个下载 FASTA 序列 ----
    with open(fasta_file, "w") as out_f:
        for acc in accessions:
            params = {
                "db": "nuccore",          # 核酸数据库
                "id": acc,                # accession 编号
                "rettype": "fasta",       # 返回 FASTA 格式
                "retmode": "text",        # 纯文本模式
                "email": _ENTREZ_EMAIL,   # NCBI 要求的邮箱标识
                "tool": "biojson_rag",    # 工具标识
            }
            r = requests.get(_ENTREZ_EFETCH_URL, params=params, timeout=30)
            r.raise_for_status()
            text = r.text.strip()

            # 验证返回的确实是 FASTA 格式（以 > 开头）
            if not text.startswith(">"):
                logger.warning("accession %s 返回非 FASTA 格式，跳过", acc)
                continue

            # 简化 FASTA header 为 >accession 便于后续处理
            lines = text.splitlines()
            lines[0] = f">{acc}"
            out_f.write("\n".join(lines) + "\n")

            # NCBI 速率限制：每秒不超过 3 次请求
            time.sleep(0.34)

    # ---- 检查是否成功下载到序列 ----
    if fasta_file.stat().st_size == 0:
        raise ValueError("未能下载到任何基因序列")

    return fasta_file
