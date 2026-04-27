from __future__ import annotations

import csv
import logging
from collections.abc import Iterator
from pathlib import Path

import requests
from lxml import etree

logger = logging.getLogger(__name__)

_URL = "http://crispr.hzau.edu.cn/cgi-bin/CRISPR2/CRISPR"
_TIMEOUT = 30
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    )
}
_OUTPUT_COLUMNS = ["Seq_name", "On_score", "Target_number", "Sequence", "PAM", "Region", "%GC", "Sequence_RC"]


def _parse_fasta(path: Path) -> Iterator[tuple[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"FASTA 文件不存在: {path}")
    header = None
    sequence_lines: list[str] = []
    with path.open(encoding="utf-8") as file:
        for line_number, raw_line in enumerate(file, start=1):
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if header is not None:
                    yield header, _validate_sequence("".join(sequence_lines), header)
                header = line[1:].strip() or f"record_at_line_{line_number}"
                sequence_lines = []
            elif header is None:
                raise ValueError(f"FASTA 格式错误：第 {line_number} 行在 header 前出现序列内容。")
            else:
                sequence_lines.append(line)
    if header is None:
        raise ValueError("FASTA 文件为空，或未找到有效记录。")
    yield header, _validate_sequence("".join(sequence_lines), header)


def _validate_sequence(sequence: str, name: str) -> str:
    cleaned = sequence.strip().replace(" ", "")
    if not cleaned:
        raise ValueError(f"序列为空: {name}")
    invalid = sorted(set(cleaned) - set("ACGTNacgtn"))
    if invalid:
        raise ValueError(f"序列 {name} 含有非法字符: {', '.join(invalid)}；仅允许 A/C/G/T/N")
    return cleaned


def _reverse_complement(sequence: str) -> str:
    return sequence.translate(str.maketrans("ACGTNacgtn", "TGCANtgcan"))[::-1]


def _fetch_result_page(sequence: str) -> str:
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


def _extract_rows(html_text: str) -> list[dict[str, str]]:
    html = etree.HTML(html_text, parser=etree.HTMLParser())
    if html is None:
        raise ValueError("HTML 解析失败。")
    rows = html.xpath('//tr[contains(@class, "guideMouseOver") and contains(@class, "seqFmt")]')
    results = []
    for row in rows:
        texts = [item.strip() for item in row.xpath("./td//text()") if item.strip()]
        if len(texts) < 6:
            continue
        target_number, on_score, sequence, pam, region, gc = texts[:6]
        results.append(
            {
                "Target_number": target_number,
                "On_score": on_score,
                "Sequence": sequence,
                "PAM": pam,
                "Region": region,
                "%GC": gc,
                "Sequence_RC": _reverse_complement(sequence),
            }
        )
    return results


def _find_first_exon_row(rows: list[dict[str, str]]) -> dict[str, str] | None:
    return next((row for row in rows if row["Region"].strip().lower() == "exon"), None)


def _write_table(path: Path, rows: list[dict[str, str]], sep: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=_OUTPUT_COLUMNS, delimiter=sep)
        writer.writeheader()
        writer.writerows(rows)


def run_crispr_target(fasta_file: Path, work_dir: Path) -> Path:
    target_file = work_dir / "crispr_target_recommended.txt"
    output_rows = []
    for seq_name, sequence in _parse_fasta(fasta_file):
        try:
            exon_row = _find_first_exon_row(_extract_rows(_fetch_result_page(sequence)))
            if exon_row is None:
                logger.warning("Sequence %s has no exon CRISPR target", seq_name)
                continue
            output_rows.append({"Seq_name": seq_name, **exon_row})
        except Exception as exc:
            logger.warning("CRISPR target design failed for %s: %s", seq_name, exc)
    if not output_rows:
        raise ValueError("未能为任何序列获取 CRISPR 靶点")
    _write_table(target_file, output_rows, "\t")
    return target_file


__all__ = ["run_crispr_target"]
