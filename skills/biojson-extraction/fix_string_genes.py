#!/usr/bin/env python3
"""修复 extraction.json 中的字符串数组问题。

当 LLM 返回字符串数组而非对象数组时，此脚本尝试从字符串中解析出基因名，
并将其转为 {"Gene_Name": "..."} 的最小对象格式。

注意：这只是应急修复，丢失了大量字段信息。推荐用 rollback + 重跑 获得完整数据。

用法:
  python skills/biojson-extraction/fix_string_genes.py           # 扫描所有，仅报告
  python skills/biojson-extraction/fix_string_genes.py --fix     # 实际执行修复
"""

import json
import os
import re
import sys

REPORTS_DIR = os.getenv("REPORTS_DIR", "/data/haotianwu/biojson/reports")
GENE_KEYS = ("Common_Genes", "Pathway_Genes", "Regulation_Genes")

DRY_RUN = "--fix" not in sys.argv


def parse_gene_string(s):
    """尝试从描述字符串中提取基因名，构建最小对象。

    常见格式:
      "OsGSTU (glutathione S-transferase, transporter gene; ...)"
      "CHS - chalcone synthase; catalyzes the first step..."
      "MYB12/SlMYB12: transcription factor regulating..."
    """
    # 尝试匹配开头的基因名（大写字母+数字，可含斜杠）
    m = re.match(r'^([A-Za-z][A-Za-z0-9_/.-]+)', s.strip())
    gene_name = m.group(1).rstrip(".:;,- ") if m else "Unknown"

    # 尝试提取括号中的描述作为 protein family
    paren = re.search(r'\(([^)]+)\)', s)
    protein_desc = paren.group(1).strip() if paren else "NA"

    return {
        "Gene_Name": gene_name,
        "Protein_Family_or_Domain": protein_desc,
        "_original_string": s,  # 保留原始字符串供参考
    }


def fix_file(path):
    """修复单个 extraction.json，返回 (修复数, 问题描述列表)。"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        return 0, ["顶层不是 dict"]

    fixes = 0
    issues = []

    for key in GENE_KEYS:
        arr = data.get(key)
        if not isinstance(arr, list):
            continue

        new_arr = []
        key_fixes = 0
        for item in arr:
            if isinstance(item, str):
                new_arr.append(parse_gene_string(item))
                key_fixes += 1
            else:
                new_arr.append(item)

        if key_fixes > 0:
            issues.append(f"{key}: {key_fixes} 个字符串 → 对象")
            fixes += key_fixes
            data[key] = new_arr

    if fixes > 0 and not DRY_RUN:
        # 备份原文件
        backup_path = path + ".bak"
        if not os.path.exists(backup_path):
            with open(path, "r", encoding="utf-8") as f:
                original = f.read()
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(original)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    return fixes, issues


def main():
    if DRY_RUN:
        print("🔍 干跑模式（仅报告，不修改文件）")
        print("   添加 --fix 参数实际执行修复\n")
    else:
        print("🔧 修复模式（将修改文件，原文件备份为 .bak）\n")

    if not os.path.exists(REPORTS_DIR):
        print(f"❌ 报告目录不存在: {REPORTS_DIR}")
        sys.exit(1)

    total_fixes = 0
    problem_files = 0

    for dirname in sorted(os.listdir(REPORTS_DIR)):
        extraction_path = os.path.join(REPORTS_DIR, dirname, "extraction.json")
        if not os.path.isfile(extraction_path):
            continue

        fixes, issues = fix_file(extraction_path)

        if fixes > 0:
            problem_files += 1
            total_fixes += fixes
            action = "已修复" if not DRY_RUN else "待修复"
            print(f"  {'🔧' if not DRY_RUN else '⚠️ '} {dirname} ({action} {fixes} 个基因)")
            for issue in issues:
                print(f"     {issue}")

    print(f"\n{'='*50}")
    print(f"扫描完毕: {problem_files} 个问题文件, {total_fixes} 个字符串基因")
    if DRY_RUN and total_fixes > 0:
        print(f"\n💡 运行以下命令执行修复:")
        print(f"   python skills/biojson-extraction/fix_string_genes.py --fix")
        print(f"\n⚠️  注意：修复只能提取基因名，大量字段会丢失。")
        print(f"   推荐方案：rollback 问题文件后重新提取。")


if __name__ == "__main__":
    main()
