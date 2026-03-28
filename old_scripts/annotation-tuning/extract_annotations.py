#!/usr/bin/env python3
"""
提取 annotation-tuning 目录下每个 JSON 文件中的"有用信息"。

有用信息定义：
  某个字段的 _comments 不为空 OR _eval 不为空且不为 "good"

输出：
  - extract_annotations.csv  （每行为一个有问题的字段）
  - extract_annotations.json （按文件/基因条目组织的汇总）
"""

import json
import csv
import os
import sys
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent          # annotation-tuning/
OUTPUT_CSV  = SCRIPT_DIR / "extract_annotations.csv"
OUTPUT_JSON = SCRIPT_DIR / "extract_annotations.json"

GENE_CATEGORIES = ["Common_Genes", "Pathway_Genes", "Regulation_Genes"]

# ──────────────────────────────────────────────────────────────
# 判断一个字段是否"有用"
# ──────────────────────────────────────────────────────────────
def is_useful(comment_val, eval_val):
    """
    _comments 不为空  OR  _eval 不为空且不为 'good'
    """
    comment_nonempty = bool(str(comment_val).strip())
    eval_nonempty_not_good = bool(str(eval_val).strip()) and str(eval_val).strip().lower() != "good"
    return comment_nonempty or eval_nonempty_not_good


# ──────────────────────────────────────────────────────────────
# 处理单个 JSON 文件
# ──────────────────────────────────────────────────────────────
def process_file(filepath: Path):
    """
    返回该文件中所有有用字段的列表，每条记录为 dict。
    """
    with open(filepath, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[WARNING] 无法解析 {filepath.name}: {e}", file=sys.stderr)
            return []

    filename = filepath.name
    title    = data.get("Title", "")
    journal  = data.get("Journal", "")
    doi      = data.get("DOI", "")

    records = []

    for category in GENE_CATEGORIES:
        gene_list = data.get(category, [])
        if not isinstance(gene_list, list):
            continue

        for idx, entry in enumerate(gene_list):
            if not isinstance(entry, dict):
                continue

            gene_name    = entry.get("Gene_Name", "")
            species_name = entry.get("Species_Latin_Name", "")
            comments_obj = entry.get("_comments", {})
            eval_obj     = entry.get("_eval", {})

            if not isinstance(comments_obj, dict):
                comments_obj = {}
            if not isinstance(eval_obj, dict):
                eval_obj = {}

            # 收集所有字段（排除 _comments / _eval 本身）
            all_fields = [k for k in entry.keys() if not k.startswith("_")]

            for field in all_fields:
                comment_val = comments_obj.get(field, "")
                eval_val    = eval_obj.get(field, "")

                if is_useful(comment_val, eval_val):
                    records.append({
                        "filename":     filename,
                        "title":        title,
                        "journal":      journal,
                        "doi":          doi,
                        "category":     category,
                        "entry_index":  idx,
                        "gene_name":    gene_name,
                        "species":      species_name,
                        "field":        field,
                        "field_value":  str(entry.get(field, "")),
                        "comment":      str(comment_val),
                        "eval":         str(eval_val),
                    })

    return records


# ──────────────────────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────────────────────
def main():
    json_files = sorted(SCRIPT_DIR.glob("*.json"))
    # 排除自身输出文件（如果有）
    json_files = [f for f in json_files if "extract_annotations" not in f.name]

    if not json_files:
        print("未找到任何 JSON 文件。")
        return

    all_records = []
    for fp in json_files:
        print(f"处理: {fp.name}")
        records = process_file(fp)
        all_records.extend(records)
        print(f"  → 找到 {len(records)} 条有用字段")

    print(f"\n共计: {len(all_records)} 条有用字段，来自 {len(json_files)} 个文件")

    # ── 写 CSV ──────────────────────────────────────────────
    csv_fields = [
        "filename", "title", "journal", "doi",
        "category", "entry_index", "gene_name", "species",
        "field", "field_value", "comment", "eval",
    ]
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()
        writer.writerows(all_records)
    print(f"CSV 已保存: {OUTPUT_CSV}")

    # ── 写 JSON（按文件 → 基因分类 → 条目 聚合）──────────────
    # 结构：{ filename: { category: [ {entry_index, gene_name, species, useful_fields:[...]} ] } }
    aggregated = {}
    for rec in all_records:
        fn  = rec["filename"]
        cat = rec["category"]
        idx = rec["entry_index"]

        if fn not in aggregated:
            aggregated[fn] = {
                "_meta": {
                    "title":   rec["title"],
                    "journal": rec["journal"],
                    "doi":     rec["doi"],
                }
            }
        if cat not in aggregated[fn]:
            aggregated[fn][cat] = {}
        if idx not in aggregated[fn][cat]:
            aggregated[fn][cat][idx] = {
                "gene_name":    rec["gene_name"],
                "species":      rec["species"],
                "useful_fields": [],
            }
        aggregated[fn][cat][idx]["useful_fields"].append({
            "field":       rec["field"],
            "field_value": rec["field_value"],
            "comment":     rec["comment"],
            "eval":        rec["eval"],
        })

    # 将嵌套 dict 中的 int key 转成 str（JSON 要求）
    def convert_keys(obj):
        if isinstance(obj, dict):
            return {str(k): convert_keys(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [convert_keys(i) for i in obj]
        return obj

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(convert_keys(aggregated), f, ensure_ascii=False, indent=2)
    print(f"JSON 已保存: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
