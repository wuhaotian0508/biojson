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
    """
    逐条解析 FASTA 文件，以生成器形式返回每条记录。

    FASTA 格式规范：
    - 以 ">" 开头的行为 header 行，">" 后的内容为序列名
    - header 之后的连续非空行为该记录的序列（可多行）
    - 每遇到新的 ">" 行，代表前一条记录结束、新记录开始

    参数:
        path: FASTA 文件路径

    Yields:
        (seq_name, sequence) 元组，其中：
        - seq_name: header 行中 ">" 之后的内容（已去除首尾空白）
        - sequence: 大写/小写混合的核酸序列字符串（不含换行符）

    异常:
        FileNotFoundError: 文件不存在
        ValueError: 文件格式错误（序列出现在 header 之前）或文件为空
    """
    if not path.exists():
        raise FileNotFoundError(f"FASTA 文件不存在: {path}")

    header: Optional[str] = None    # header: 当前记录的序列名；None 表示还未读到第一条记录
    seq_lines: List[str] = []       # seq_lines: 当前记录的序列行列表（多行拼接用）

    with path.open("r", encoding="utf-8") as f:
        for line_num, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue   # 跳过空行

            if line.startswith(">"):
                # 遇到新 header：先 yield 上一条完整记录（如果有）
                if header is not None:
                    yield header, _validate_sequence("".join(seq_lines), header)
                # 更新 header 和序列缓冲区
                header = line[1:].strip() or f"record_at_line_{line_num}"
                seq_lines = []
            else:
                # 序列行：必须在 header 之后出现
                if header is None:
                    raise ValueError(f"FASTA 格式错误：第 {line_num} 行在 header 前出现序列内容。")
                seq_lines.append(line)

    # 文件末尾 yield 最后一条记录
    if header is not None:
        yield header, _validate_sequence("".join(seq_lines), header)
    else:
        raise ValueError("FASTA 文件为空，或未找到有效记录。")


def _validate_sequence(sequence: str, name: str) -> str:
    """
    验证核酸序列的合法性并返回清洗后的序列。

    检查规则：
    1. 去除首尾空白和内部空格
    2. 不允许空序列
    3. 只允许 A/C/G/T/N（大小写均可），其他字符视为非法

    参数:
        sequence: 原始序列字符串（可能含空格、混合大小写）
        name:     序列名（仅用于错误信息）

    返回:
        清洗后的序列字符串（保留原始大小写，去除空格）

    异常:
        ValueError: 序列为空或含非法字符时
    """
    cleaned = sequence.strip().replace(" ", "")   # cleaned: 去除空格后的序列
    if not cleaned:
        raise ValueError(f"序列为空: {name}")

    allowed = set("ACGTNacgtn")           # allowed: 合法字符集合
    invalid = sorted(set(cleaned) - allowed)  # invalid: 序列中存在的非法字符（排序便于展示）
    if invalid:
        raise ValueError(f"序列 {name} 含有非法字符: {', '.join(invalid)}；仅允许 A/C/G/T/N")

    return cleaned


def _reverse_complement(seq: str) -> str:
    """
    计算核酸序列的反向互补序列。

    反向互补 = 先做碱基互补（A↔T，C↔G，N↔N），再将整条序列反转。
    在 CRISPR 实验中，设计 guide RNA 时需要知道靶点序列的反向互补，
    以便合成对应的 oligo（引导 RNA 的正反链）。

    参数:
        seq: 核酸序列字符串，支持大小写混合

    返回:
        反向互补序列字符串（大小写与输入一致）
    """
    # trans: 字符替换映射表，A↔T，C↔G，N↔N（大小写分别处理）
    trans = str.maketrans({
        "A": "T", "T": "A", "C": "G", "G": "C", "N": "N",
        "a": "t", "t": "a", "c": "g", "g": "c", "n": "n",
    })
    return seq.translate(trans)[::-1]   # 先碱基互补，再 [::-1] 反转


def _fetch_result_page(sequence: str) -> str:
    """
    将核酸序列提交到华中农大 CRISPR 设计网站，返回结果 HTML 页面。

    网站使用 POST 表单提交，固定参数包括：
    - pam: "NGG"  — 使用 SpCas9 的 NGG PAM 位点
    - oligo: "U3"  — U3 启动子（驱动 gRNA 表达的常用启动子）
    - template: sgRNA 骨架序列（通用 scaffold）
    - spacer_length: 20  — 靶点间隔序列长度（标准 20bp）
    - 其他参数为数据库/位置占位符（网站必填但不影响靶点计算结果）

    参数:
        sequence: 待分析的核酸序列（FASTA 序列部分，不含 header）

    返回:
        CRISPR 网站返回的 HTML 结果页面文本

    异常:
        RuntimeError: 网络请求失败（包括超时、HTTP 错误等）
    """
    payload = {
        "pam": "NGG",                    # PAM 类型：SpCas9 识别的 NGG 序列
        "oligo": "U3",                   # 启动子类型：U3（常用于植物 gRNA 表达）
        # template: sgRNA 通用骨架序列（tracrRNA 部分），引导 Cas9 与 gRNA 结合
        "template": "GUUUUAGAGCUAGAAAUAGCAAGUUAAAAUAAGGCUAGUCCGUUAUCAACUUGAAAAAGUGGCACCGAGUCGGUGCUUUU",
        "spacer_length": 20,             # 靶点序列长度（bp），标准为 20bp
        "name_db": "Actinidia_chinensis", # 数据库名称占位符（网站必填参数）
        "loc": "CEY00_Acc00114",          # 基因组位置占位符
        "position": "CM009654.1:41843..42575",   # 坐标占位符
        "sequence": sequence,            # 待设计靶点的核酸序列
        ".submit": "Submit",             # 表单提交按钮值
        ".cgifields": "oligo",           # CGI 字段标识
    }
    try:
        response = requests.post(_URL, data=payload, headers=_HEADERS, timeout=_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"请求失败: {exc}") from exc
    return response.text


def _extract_rows(html_text: str) -> List[Dict[str, str]]:
    """
    从 CRISPR 网站的 HTML 结果页中提取候选靶点数据。

    网站将每个候选靶点显示为一个 <tr> 行，class 同时含有
    "guideMouseOver" 和 "seqFmt"。每行的 <td> 单元格按顺序包含：
    靶点编号、On-target 评分、靶点序列、PAM、区域（exon/intron 等）、GC 含量。

    同时计算每条靶点序列的反向互补序列（Sequence_RC），
    用于后续合成 oligo 时的引物设计。

    参数:
        html_text: CRISPR 网站返回的完整 HTML 页面文本

    返回:
        候选靶点字典列表，每项包含：
        - Target_number: 靶点编号（如 "1"）
        - On_score:      on-target 预测评分（越高越好）
        - Sequence:      20bp 正向靶点序列
        - PAM:           PAM 序列（如 "NGG"）
        - Region:        基因组区域类型（"exon"/"intron"/"intergenic" 等）
        - %GC:           GC 含量百分比
        - Sequence_RC:   靶点序列的反向互补序列

    异常:
        ValueError: HTML 解析失败（页面结构异常）
    """
    parser = etree.HTMLParser()
    html = etree.HTML(html_text, parser=parser)   # html: 解析后的 HTML 元素树
    if html is None:
        raise ValueError("HTML 解析失败。")

    # 定位所有候选靶点行（同时具有 guideMouseOver 和 seqFmt 两个 class 的 <tr>）
    rows = html.xpath(
        '//tr[contains(@class, "guideMouseOver") and contains(@class, "seqFmt")]'
    )

    results: List[Dict[str, str]] = []
    for row in rows:
        # texts: 该行所有可见文本内容（去除空白后）
        texts = [x.strip() for x in row.xpath("./td//text()") if x.strip()]
        if len(texts) < 6:
            continue   # 列数不足，跳过格式异常的行

        # 按列顺序解包：编号、评分、序列、PAM、区域、GC 含量
        target_number, on_score, sequence, pam, region, gc = texts[:6]
        results.append({
            "Target_number": target_number,   # 靶点序号（网站内部编号）
            "On_score": on_score,             # on-target 评分（预测切割效率）
            "Sequence": sequence,             # 20bp 正向 spacer 序列
            "PAM": pam,                       # PAM 序列（紧接 spacer 的 3' 端）
            "Region": region,                 # 基因组区域（exon/intron 等）
            "%GC": gc,                        # GC 含量（%），过高或过低的 GC 会影响效率
            "Sequence_RC": _reverse_complement(sequence),   # 反向互补序列（用于合成 oligo）
        })
    return results


def _find_first_exon_row(rows: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """
    从候选靶点列表中找到第一个位于 exon 区域的靶点。

    优先选择 exon 区域靶点的原因：
    - Exon 区突变通常导致功能丧失（移码突变或氨基酸替换），
      比 intron 突变更可靠地产生基因敲除表型
    - Intron 突变可能被剪接机制修复，表型不稳定

    参数:
        rows: _extract_rows() 返回的候选靶点字典列表

    返回:
        第一个 Region 为 "exon"（不区分大小写）的靶点字典；
        未找到时返回 None
    """
    for row in rows:
        if row["Region"].strip().lower() == "exon":
            return row
    return None


def _build_output_row(seq_name: str, row: Dict[str, str]) -> Dict[str, str]:
    """
    将序列名和靶点数据合并为输出格式的一行字典。

    参数:
        seq_name: FASTA 序列名（来自 header 行），即 accession 编号
        row:      _find_first_exon_row() 返回的靶点字典

    返回:
        包含 Seq_name + 靶点所有字段的字典，字段顺序与 _OUTPUT_COLUMNS 一致
    """
    return {
        "Seq_name": seq_name,                    # 序列标识（来自 FASTA header）
        "Target_number": row["Target_number"],   # 靶点编号
        "On_score": row["On_score"],             # 预测评分
        "Sequence": row["Sequence"],             # 正向 20bp 序列
        "PAM": row["PAM"],                       # PAM 序列
        "Region": row["Region"],                 # 区域类型（这里固定为 exon）
        "%GC": row["%GC"],                       # GC 含量
        "Sequence_RC": row["Sequence_RC"],       # 反向互补序列
    }


def _write_table(path: Path, rows: List[Dict[str, str]], sep: str) -> None:
    """
    将靶点数据写入制表符分隔的 TSV 文件。

    使用 csv.DictWriter 保证列顺序与 _OUTPUT_COLUMNS 一致，
    并自动写入表头行。

    参数:
        path: 输出文件路径
        rows: 靶点字典列表（每项的键需包含 _OUTPUT_COLUMNS 中所有列名）
        sep:  分隔符，通常为 "\t"（TSV）
    """
    with path.open("w", encoding="utf-8", newline="") as f:
        # fieldnames: 控制列的输出顺序
        writer = csv.DictWriter(f, fieldnames=_OUTPUT_COLUMNS, delimiter=sep)
        writer.writeheader()   # 写入表头
        writer.writerows(rows) # 写入所有数据行


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
