#!/usr/bin/env python3
import argparse
import requests
import time
import sys

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def fetch_fasta(accession, email, tool):
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
    lines = fasta_text.splitlines()
    lines[0] = f">{accession}"  # 替换header
    return "\n".join(lines)


def read_accessions(file_path, col_index=2, sep=None):
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