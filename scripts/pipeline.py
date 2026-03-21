"""
pipeline.py — 流水线协调器

每篇论文 3 次硬编码 API 调用：
  API #1: classify_genes     → 读取 MD，分类基因，构建 gene_dict
  API #2: extract_*_genes    → 根据分类提取详细字段
  API #3: verify_all_genes   → 验证所有字段的忠实度

代码控制每步调哪个 tool（不依赖 LLM 自由选择）。

用法：
    python scripts/pipeline.py          # 全量处理
    TEST_MODE=1 python scripts/pipeline.py  # 测试模式
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 确保 scripts/ 在 path 中
sys.path.insert(0, os.path.join(os.getenv("BASE_DIR", "/data/haotianwu/biojson"), "scripts"))

from md_to_json import extract_paper, resolve_test_files, tracker as extract_tracker, failed_files
from verify_response import verify_paper, print_summary, tracker as verify_tracker
from token_tracker import TokenTracker

BASE_DIR = os.getenv("BASE_DIR", "/data/haotianwu/biojson")
MD_DIR = os.getenv("MD_DIR", os.path.join(BASE_DIR, "md"))
TOKEN_USAGE_DIR = os.getenv("TOKEN_USAGE_DIR", os.path.join(BASE_DIR, "token-usage"))


def main():
    print("═" * 60)
    print("🚀 BioJSON Pipeline v3 — 3 次硬编码 API 调用/篇")
    print("   API #1: classify_genes → 分类")
    print("   API #2: extract_*_genes → 提取详细字段")
    print("   API #3: verify_all_genes → 验证忠实度")
    print("═" * 60)

    if not os.path.exists(MD_DIR):
        print(f"❌ 输入目录不存在: {MD_DIR}")
        return

    files = sorted([f for f in os.listdir(MD_DIR) if f.endswith('.md')])
    print(f"📂 找到 {len(files)} 个待处理文件")

    if os.getenv("TEST_MODE") == "1":
        files = resolve_test_files(files)
        if not files:
            return

    all_reports = []

    for i, filename in enumerate(files, 1):
        md_path = os.path.join(MD_DIR, filename)
        stem = os.path.splitext(filename)[0]

        print(f"\n{'━' * 60}")
        print(f"📄 [{i}/{len(files)}] {filename}")
        print(f"{'━' * 60}")

        # ── API #1 + #2：分类 + 提取 ──
        print(f"\n  🔷 API #1 + #2：分类 + 提取基因...")
        extraction, gene_dict = extract_paper(md_path)

        if extraction is None:
            print(f"  ❌ 提取失败，跳过验证: {filename}")
            continue

        total_genes = sum(
            len(extraction.get(k, []))
            for k in ("Common_Genes", "Pathway_Genes", "Regulation_Genes")
        )
        print(f"  📊 提取到 {total_genes} 个基因, 分类: {gene_dict}")

        # ── API #3：验证 ──
        print(f"\n  🔷 API #3：验证基因...")
        report = verify_paper(md_path, extraction, gene_dict, stem)

        if report:
            all_reports.append(report)
            s = report["summary"]
            print(f"\n  📈 {stem}: 忠实度 {s['supported']}/{s['total_fields']} "
                  f"({s['supported']/s['total_fields']*100:.0f}%) | "
                  f"修正 {s['total_corrections']} 个字段")

    # ── 汇总 ──
    if all_reports:
        print_summary(all_reports)

    # 合并 token 用量
    combined = TokenTracker(model=os.getenv("MODEL", "Vendor2/Claude-4.6-opus"))
    combined.merge(extract_tracker)
    combined.merge(verify_tracker)
    combined.print_summary()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    combined.save_report(os.path.join(TOKEN_USAGE_DIR, f"pipeline-{timestamp}.json"))

    if failed_files:
        print(f"\n⚠️  {len(failed_files)} 个文件提取失败: {failed_files}")
        print(f"   提示: FORCE_RERUN=1 bash scripts/run.sh pipeline")

    print(f"\n✅ Pipeline 完成！处理 {len(files)} 篇, 验证 {len(all_reports)} 篇")


if __name__ == "__main__":
    main()
