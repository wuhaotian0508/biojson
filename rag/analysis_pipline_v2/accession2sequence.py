#!/usr/bin/env python3
import argparse
import requests
import time
import sys

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# 这个脚本的作用：
# 1. 从上一步输出的表格中读取 accession；
# 2. 调用 NCBI efetch 接口下载对应 FASTA 序列；
# 3. 对 FASTA 的 header 做简化；
# 4. 把多个序列合并写入一个 fasta 文件。


def fetch_fasta(accession, email, tool):
    """
    根据 accession 从 NCBI Nuccore 拉取 FASTA 文本。

    输入：
    - accession: 核酸序列 accession
    - email: 请求时附带的邮箱，用于符合 NCBI 使用建议
    - tool: 工具名标识

    输出：
    - 原始 FASTA 文本

    异常处理：
    - 如果 HTTP 请求失败，会抛出 requests 异常；
    - 如果返回内容不像 FASTA（没有以 '>' 开头），会主动抛错。
    """
    params = {
        "db": "nuccore",
        "id": accession,
        "rettype": "fasta",
        "retmode": "text",
        "email": email,
        "tool": tool
    }

    r = requests.get(BASE_URL, params=params, timeout=30)
    r.raise_for_status()

    text = r.text.strip()
    if not text.startswith(">"):
        raise ValueError(f"返回内容不是FASTA: {accession}")

    return text


def simplify_header(fasta_text, accession):
    """
    把 FASTA 第一行 header 简化成 >accession。

    为什么要做这一步：
    - NCBI 返回的 FASTA header 往往很长；
    - 下游处理通常只需要 accession 作为序列名；
    - 简化后更方便后续 CRISPR 结果和 accession 一一对应。
    """
    lines = fasta_text.splitlines()
    lines[0] = f">{accession}"  # 替换header
    return "\n".join(lines)


def read_accessions(file_path, col_index=2, sep=None):
    """
    从表格文件中读取 accession 列。

    默认读取第 3 列（索引 2），因为上一步 gene2accession.py
    输出的是：gene_name, species_name, accession。

    行为说明：
    - 跳过空行；
    - 如果某一行列数不足，则跳过；
    - 返回 accession 字符串列表。
    """
    accessions = []
    with open(file_path) as f:
        for line in f:
            if not line.strip():
                continue
            parts = line.strip().split(sep)
            if len(parts) <= col_index:
                continue
            accessions.append(parts[col_index])
    return accessions


def main():
    """
    accession2sequence.py 的主函数。

    运行顺序：
    1. 解析参数；
    2. 从输入表格读取 accession 列表；
    3. 对每个 accession 调 fetch_fasta 下载序列；
    4. 用 simplify_header 简化标题；
    5. 逐条写入输出 FASTA 文件；
    6. 每次请求后 sleep，避免请求过快。
    """
    parser = argparse.ArgumentParser(
        description="从三列表格读取accession（第3列），下载FASTA并合并输出"
    )

    parser.add_argument("-i", "--input", required=True, help="输入表格文件")
    parser.add_argument("-o", "--output", required=True, help="输出FASTA文件")
    parser.add_argument("--sep", default="\t", help="分隔符（默认tab）")
    parser.add_argument("--email", default="your_email@example.com")
    parser.add_argument("--tool", default="table_to_fasta")
    parser.add_argument("--delay", type=float, default=0.34)

    args = parser.parse_args()

    accessions = read_accessions(args.input, col_index=2, sep=args.sep)

    if not accessions:
        print("未读取到accession", file=sys.stderr)
        sys.exit(1)

    print(f"读取到 {len(accessions)} 个 accession: {accessions}")

    with open(args.output, "w") as out_f:
        for acc in accessions:
            try:
                fasta = fetch_fasta(acc, args.email, args.tool)
                fasta = simplify_header(fasta, acc)
                out_f.write(fasta + "\n")
                print(f"{acc} 下载成功")
            except Exception as e:
                print(f"[ERROR] {acc}: {e}", file=sys.stderr)

            time.sleep(args.delay)

    print(f"完成，输出文件: {args.output}")


if __name__ == "__main__":
    main()