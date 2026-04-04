"""
Step 3: FASTA 序列 → CRISPR 靶点

功能：读取 FASTA 序列文件，提交到华中农大 CRISPR 设计网站，
     为每条序列筛选第一个落在 exon 区域的 CRISPR 靶点。

输入：fasta_file — Step 2 生成的 FASTA 文件
     work_dir — 工作目录（Path）
输出：CRISPR 靶点 TSV 文件路径（Path）
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

import requests
from lxml import etree

logger = logging.getLogger(__name__)

_URL = "http://crispr.hzau.edu.cn/cgi-bin/CRISPR2/CRISPR"
_TIMEOUT = 30
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/146.0.0.0 Safari/537.36"
    )
}

_OUTPUT_COLUMNS = [
    "Seq_name", "On_score", "Target_number",
    "Sequence", "PAM", "Region", "%GC", "Sequence_RC",
]


# ------------------------------------------------------------------
# FASTA 解析
# ------------------------------------------------------------------

def _parse_fasta(path: Path) -> Iterator[Tuple[str, str]]:
    """逐条读取 FASTA，返回 (seq_name, sequence)。"""
    if not path.exists():
        raise FileNotFoundError(f"FASTA 文件不存在: {path}")

    header: Optional[str] = None
    seq_lines: List[str] = []

    with path.open("r", encoding="utf-8") as f:
        for line_num, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if header is not None:
                    yield header, _validate_sequence("".join(seq_lines), header)
                header = line[1:].strip() or f"record_at_line_{line_num}"
                seq_lines = []
            else:
                if header is None:
                    raise ValueError(f"FASTA 格式错误：第 {line_num} 行在 header 前出现序列内容。")
                seq_lines.append(line)

    if header is not None:
        yield header, _validate_sequence("".join(seq_lines), header)
    else:
        raise ValueError("FASTA 文件为空，或未找到有效记录。")


def _validate_sequence(sequence: str, name: str) -> str:
    cleaned = sequence.strip().replace(" ", "")
    if not cleaned:
        raise ValueError(f"序列为空: {name}")
    allowed = set("ACGTNacgtn")
    invalid = sorted(set(cleaned) - allowed)
    if invalid:
        raise ValueError(f"序列 {name} 含有非法字符: {', '.join(invalid)}；仅允许 A/C/G/T/N")
    return cleaned


def _reverse_complement(seq: str) -> str:
    """反向互补。"""
    trans = str.maketrans({
        "A": "T", "T": "A", "C": "G", "G": "C", "N": "N",
        "a": "t", "t": "a", "c": "g", "g": "c", "n": "n",
    })
    return seq.translate(trans)[::-1]


# ------------------------------------------------------------------
# CRISPR 网站交互
# ------------------------------------------------------------------

def _fetch_result_page(sequence: str) -> str:
    """提交序列到 CRISPR 网站，返回 HTML 结果页。"""
    payload = {
        "pam": "NGG",
        "oligo": "U3",
        "template": "GUUUUAGAGCUAGAAAUAGCAAGUUAAAAUAAGGCUAGUCCGUUAUCAACUUGAAAAAGUGGCACCGAGUCGGUGCUUUU",
        "spacer_length": 20,
        "name_db": "Actinidia_chinensis",
        "loc": "CEY00_Acc00114",
        "position": "CM009654.1:41843..42575",
        "sequence": sequence,
        ".submit": "Submit",
        ".cgifields": "oligo",
    }
    try:
        response = requests.post(_URL, data=payload, headers=_HEADERS, timeout=_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"请求失败: {exc}") from exc
    return response.text


def _extract_rows(html_text: str) -> List[Dict[str, str]]:
    """从 HTML 结果页提取候选靶点。"""
    parser = etree.HTMLParser()
    html = etree.HTML(html_text, parser=parser)
    if html is None:
        raise ValueError("HTML 解析失败。")

    rows = html.xpath(
        '//tr[contains(@class, "guideMouseOver") and contains(@class, "seqFmt")]'
    )
    results: List[Dict[str, str]] = []
    for row in rows:
        texts = [x.strip() for x in row.xpath("./td//text()") if x.strip()]
        if len(texts) < 6:
            continue
        target_number, on_score, sequence, pam, region, gc = texts[:6]
        results.append({
            "Target_number": target_number,
            "On_score": on_score,
            "Sequence": sequence,
            "PAM": pam,
            "Region": region,
            "%GC": gc,
            "Sequence_RC": _reverse_complement(sequence),
        })
    return results


def _find_first_exon_row(rows: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    for row in rows:
        if row["Region"].strip().lower() == "exon":
            return row
    return None


def _build_output_row(seq_name: str, row: Dict[str, str]) -> Dict[str, str]:
    return {
        "Seq_name": seq_name,
        "Target_number": row["Target_number"],
        "On_score": row["On_score"],
        "Sequence": row["Sequence"],
        "PAM": row["PAM"],
        "Region": row["Region"],
        "%GC": row["%GC"],
        "Sequence_RC": row["Sequence_RC"],
    }


def _write_table(path: Path, rows: List[Dict[str, str]], sep: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_OUTPUT_COLUMNS, delimiter=sep)
        writer.writeheader()
        writer.writerows(rows)


# ------------------------------------------------------------------
# 公开接口
# ------------------------------------------------------------------

def run_crispr_target(fasta_file: Path, work_dir: Path) -> Path:
    """
    设计 CRISPR 靶点。

    参数:
        fasta_file: Step 2 生成的 FASTA 序列文件
        work_dir: 临时工作目录

    返回:
        CRISPR 靶点 TSV 文件路径

    异常:
        ValueError: 当未能为任何序列获取到 exon 区靶点时抛出
    """
    target_file = work_dir / "crispr_target_recommended.txt"
    output_rows = []

    for seq_name, sequence in _parse_fasta(fasta_file):
        try:
            html_text = _fetch_result_page(sequence)
            all_rows = _extract_rows(html_text)
            exon_row = _find_first_exon_row(all_rows)

            if exon_row is None:
                logger.warning("序列 %s 未找到 exon 区域的 CRISPR 靶点", seq_name)
                continue

            output_rows.append(_build_output_row(seq_name, exon_row))
        except Exception as e:
            logger.warning("序列 %s 的 CRISPR 靶点设计失败: %s", seq_name, e)

    if not output_rows:
        raise ValueError("未能为任何序列获取 CRISPR 靶点")

    _write_table(target_file, output_rows, "\t")
    return target_file
