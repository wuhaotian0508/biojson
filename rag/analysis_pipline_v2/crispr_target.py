#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

import requests
from lxml import etree


# 这个脚本的作用：
# 1. 读取 FASTA 文件中的每条核酸序列；
# 2. 将序列提交到外部 CRISPR 设计网站；
# 3. 解析网页结果表格；
# 4. 为每条序列选取第一个 Region == exon 的候选靶点；
# 5. 输出成 TSV 表格，供后续实验方案拼装使用。


URL = "http://crispr.hzau.edu.cn/cgi-bin/CRISPR2/CRISPR"
DEFAULT_TIMEOUT = 30
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/146.0.0.0 Safari/537.36"
    )
}

OUTPUT_COLUMNS = [
    "Seq_name",
    "On_score",
    "Target_number",
    "Sequence",
    "PAM",
    "Region",
    "%GC",
    "Sequence_RC",
]


def build_parser() -> argparse.ArgumentParser:
    """
    构建命令行参数解析器。

    参数很简单：
    - 输入 FASTA 文件
    - 输出 TSV 文件
    - 输出分隔符
    """
    parser = argparse.ArgumentParser(
        description="从 FASTA 文件读取多条序列，提交 CRISPR 网站，并为每条序列输出第一个 Region == exon 的结果。"
    )
    parser.add_argument("-i", "--input", required=True, help="输入FASTA文件")
    parser.add_argument("-o", "--output", required=True, help="输出TSV文件")
    parser.add_argument("--sep", default="\t", help="分隔符（默认tab）")
    return parser


def parse_fasta(path: Path) -> Iterator[Tuple[str, str]]:
    """
    逐条读取 FASTA，返回 (seq_name, sequence)

    功能说明：
    - 手动解析 FASTA 文件；
    - 每遇到一个新的 header（以 > 开头），就把上一条记录产出；
    - 产出的结果是 (序列名, 序列字符串)。

    同时它还会：
    - 检查文件是否存在；
    - 检查格式是否合法；
    - 调用 validate_sequence 校验序列字符。
    """
    if not path.exists():
        raise FileNotFoundError(f"FASTA 文件不存在: {path}")
    if not path.is_file():
        raise ValueError(f"不是有效文件: {path}")

    header: Optional[str] = None
    seq_lines: List[str] = []

    with path.open("r", encoding="utf-8") as f:
        for line_num, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith(">"):
                if header is not None:
                    yield header, validate_sequence("".join(seq_lines), header)
                header = line[1:].strip() or f"record_at_line_{line_num}"
                seq_lines = []
            else:
                if header is None:
                    raise ValueError(
                        f"FASTA 格式错误：第 {line_num} 行在 header 前出现序列内容。"
                    )
                seq_lines.append(line)

    if header is not None:
        yield header, validate_sequence("".join(seq_lines), header)
    else:
        raise ValueError("FASTA 文件为空，或未找到有效记录。")


def validate_sequence(sequence: str, name: str) -> str:
    """
    校验并清洗 DNA 序列。

    检查点：
    - 去掉首尾空白和内部空格；
    - 不允许空序列；
    - 只允许 A/C/G/T/N（大小写都可）。

    返回：
    - 清洗后的序列字符串。

    作用：
    - 避免把非法字符提交给 CRISPR 网站导致后续解析失败。
    """
    cleaned = sequence.strip().replace(" ", "")
    if not cleaned:
        raise ValueError(f"序列为空: {name}")

    allowed = set("ACGTNacgtn")
    invalid = sorted(set(cleaned) - allowed)
    if invalid:
        raise ValueError(
            f"序列 {name} 含有非法字符: {', '.join(invalid)}；仅允许 A/C/G/T/N"
        )
    return cleaned


def reverse_complement(seq: str) -> str:
    """
    反向互补，保留大小写对应关系

    作用：
    - 对候选 guide sequence 生成反向互补序列；
    - 最终会一并写入输出结果，方便后续实验设计使用。
    """
    trans = str.maketrans({
        "A": "T", "T": "A", "C": "G", "G": "C", "N": "N",
        "a": "t", "t": "a", "c": "g", "g": "c", "n": "n",
    })
    return seq.translate(trans)[::-1]


def build_payload(sequence: str) -> dict:
    """
    构造提交给 CRISPR 网站的表单数据。

    说明：
    - 这里包含 PAM、模板、spacer_length 等参数；
    - 当前实现是写死的一组默认参数；
    - 唯一动态变化的核心字段是 sequence。

    结果：
    - 返回 requests.post 可直接使用的 data 字典。
    """
    return {
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


def fetch_result_page(sequence: str) -> str:
    """
    提交序列到外部 CRISPR 网站并获取返回 HTML。

    执行流程：
    - 调用 build_payload 构造 POST 表单；
    - 使用 requests.post 提交；
    - 如果网络或 HTTP 层失败，则抛出 RuntimeError；
    - 成功时返回原始 HTML 文本。
    """
    payload = build_payload(sequence)
    try:
        response = requests.post(
            URL,
            data=payload,
            headers=DEFAULT_HEADERS,
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"请求失败: {exc}") from exc
    return response.text


def extract_rows(html_text: str) -> List[Dict[str, str]]:
    """
    提取所有候选 row，每个 row 取前 5 列：
    Target_number, Sequence, PAM, Region, %GC
    并新增 Sequence_RC

    功能说明：
    - 从 CRISPR 网站返回的 HTML 中抽取候选靶点表格；
    - 通过 XPath 定位网页中的目标 tr；
    - 从每行中取出关键字段，并构造成字典。

    输出字段：
    - Target_number
    - On_score
    - Sequence
    - PAM
    - Region
    - %GC
    - Sequence_RC（本地额外计算）

    注意：
    - 这里是“网页解析”逻辑的核心。
    """
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
            "Sequence_RC": reverse_complement(sequence),
        })

    return results


def find_first_exon_row(rows: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """
    在候选结果中寻找第一个 Region == exon 的靶点。

    设计意图：
    - 当前脚本并不做复杂评分或排序；
    - 它只取“第一个 exon 命中结果”作为推荐靶点。

    返回：
    - 找到则返回该行字典；
    - 否则返回 None。
    """
    for row in rows:
        if row["Region"].strip().lower() == "exon":
            return row
    return None


def build_output_row(seq_name: str, row: Dict[str, str]) -> Dict[str, str]:
    """
    把内部候选结果组装成最终输出表的一行。

    作用：
    - 增加 Seq_name 字段；
    - 保证输出字段名与 OUTPUT_COLUMNS 一致；
    - 让写文件逻辑更简单、稳定。
    """
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


def write_table(path: Path, rows: List[Dict[str, str]], sep: str) -> None:
    """
    把结果列表写成表格文件。

    行为：
    - 使用 DictWriter 按固定字段顺序写出；
    - 先写表头，再写所有结果行。
    """
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, delimiter=sep)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    """
    crispr_target.py 的主函数。

    运行顺序：
    1. 解析参数；
    2. 读取输入 FASTA；
    3. 对每条序列：
       - 提交到 CRISPR 网站；
       - 解析候选结果；
       - 选择第一个 exon 靶点；
       - 组装输出行；
    4. 把所有成功结果写入输出 TSV；
    5. 将失败项输出到 stderr。

    返回值：
    - 成功返回 0；
    - 顶层异常返回 1。
    """
    parser = build_parser()
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    sep = args.sep.encode("utf-8").decode("unicode_escape")

    output_rows: List[Dict[str, str]] = []
    failed_names: List[str] = []

    try:
        for seq_name, sequence in parse_fasta(input_path):
            try:
                html_text = fetch_result_page(sequence)
                all_rows = extract_rows(html_text)
                exon_row = find_first_exon_row(all_rows)

                if exon_row is None:
                    failed_names.append(seq_name)
                    continue

                output_rows.append(build_output_row(seq_name, exon_row))
                print(f"{seq_name} 处理成功")

            except Exception as exc:
                failed_names.append(f"{seq_name} ({exc})")

        write_table(output_path, output_rows, sep)
        print(f"结果已输出到: {output_path}")

        if failed_names:
            print(
                f"警告: 有 {len(failed_names)} 条序列未获得 exon 结果或处理失败。",
                file=sys.stderr,
            )
            for name in failed_names:
                print(f"  - {name}", file=sys.stderr)

        return 0

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())