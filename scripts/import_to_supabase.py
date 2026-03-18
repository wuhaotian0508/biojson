#!/usr/bin/env python3
"""
import_to_supabase.py — 将本地 md + json + 验证报告 导入 Supabase 数据库

使用方法:
  1. pip install supabase python-dotenv
  2. 在 .env 中配置 SUPABASE_URL 和 SUPABASE_SERVICE_ROLE_KEY
  3. python scripts/import_to_supabase.py

注意: 此脚本使用 service_role key（非 anon key），因此可以绕过 RLS 写入。
"""

import os
import sys
import json
import re
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ 请在 .env 中设置 SUPABASE_URL 和 SUPABASE_SERVICE_ROLE_KEY")
    sys.exit(1)

try:
    from supabase import create_client
except ImportError:
    print("❌ 请安装 supabase: pip install supabase")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent

# 目录
MD_DIR = ROOT / "md" / "processed"
JSON_DIR = ROOT / "json"
REPORTS_DIR = ROOT / "reports"

CONFIG_NAME = "nutri_plant"


def slugify(name: str) -> str:
    """将文件名转为 URL 友好的 slug"""
    slug = re.sub(r'[^a-zA-Z0-9_-]', '-', name)
    slug = re.sub(r'-+', '-', slug).strip('-').lower()
    return slug


def find_pairs():
    """查找 md + verified json 的配对"""
    pairs = []

    for json_file in sorted(JSON_DIR.glob(f"*_{CONFIG_NAME}_verified.json")):
        # 从 JSON 文件名推断 MD 文件名
        json_stem = json_file.stem  # e.g. "full_nutri_plant_verified"
        md_stem = json_stem.replace(f"_{CONFIG_NAME}_verified", "")

        # 尝试查找对应 MD
        md_file = MD_DIR / f"{md_stem}.md"
        if not md_file.exists():
            print(f"⚠️  找不到 MD 文件: {md_file}, 跳过")
            continue

        # 查找验证报告
        report_dir = None
        # 尝试多种命名
        for d in REPORTS_DIR.iterdir():
            if d.is_dir() and (d.name == md_stem or md_stem.startswith(d.name)):
                report_dir = d
                break

        pairs.append({
            "md_file": md_file,
            "json_file": json_file,
            "report_dir": report_dir,
            "slug": slugify(md_stem),
        })

    return pairs


def extract_meta(data: dict):
    """从 JSON 中提取 Title, Journal, DOI"""
    # 适配两种结构
    inner = data.get("CropNutrientMetabolismGeneExtraction", data)
    return {
        "title": inner.get("Title"),
        "journal": inner.get("Journal"),
        "doi": inner.get("DOI"),
    }


def extract_genes(data: dict) -> list:
    """提取基因列表"""
    inner = data.get("CropNutrientMetabolismGeneExtraction", data)
    return inner.get("Genes", [])


def import_paper(pair: dict):
    slug = pair["slug"]
    print(f"\n📄 导入: {slug}")

    # 读取文件
    md_content = pair["md_file"].read_text(encoding="utf-8")
    json_data = json.loads(pair["json_file"].read_text(encoding="utf-8"))

    meta = extract_meta(json_data)
    genes_data = extract_genes(json_data)

    # 读取验证报告
    verification_report = None
    if pair["report_dir"]:
        vr_file = pair["report_dir"] / "verification.json"
        if vr_file.exists():
            verification_report = json.loads(vr_file.read_text(encoding="utf-8"))

    # 检查是否已存在
    existing = supabase.table("papers").select("id").eq("slug", slug).execute()
    if existing.data:
        paper_id = existing.data[0]["id"]
        print(f"  ⚡ 已存在，更新 paper_id={paper_id}")
        supabase.table("papers").update({
            "md_content": md_content,
            "extraction_json": json_data,
            "verified_json": json_data,
            "verification_report": verification_report,
            "title": meta["title"],
            "journal": meta["journal"],
            "doi": meta["doi"],
            "gene_count": len(genes_data),
        }).eq("id", paper_id).execute()

        # 删除旧基因重新插入
        supabase.table("genes").delete().eq("paper_id", paper_id).execute()
    else:
        result = supabase.table("papers").insert({
            "slug": slug,
            "md_content": md_content,
            "extraction_json": json_data,
            "verified_json": json_data,
            "verification_report": verification_report,
            "title": meta["title"],
            "journal": meta["journal"],
            "doi": meta["doi"],
            "gene_count": len(genes_data),
            "status": "pending",
        }).execute()
        paper_id = result.data[0]["id"]
        print(f"  ✅ 新建 paper_id={paper_id}")

    # 插入基因
    vr_genes = {}
    if verification_report and "genes" in verification_report:
        for vg in verification_report["genes"]:
            vr_genes[vg.get("gene_index", -1)] = vg

    for idx, gene_data in enumerate(genes_data):
        vg = vr_genes.get(idx, {})
        gene_row = {
            "paper_id": paper_id,
            "gene_index": idx,
            "gene_name": gene_data.get("Gene_Name"),
            "gene_data": gene_data,
            "auto_verification": vg.get("verification"),
            "auto_stats": vg.get("stats"),
        }
        supabase.table("genes").insert(gene_row).execute()

    print(f"  🧬 导入 {len(genes_data)} 个基因")


def main():
    print("=" * 60)
    print("🚀 BioJSON → Supabase 数据导入")
    print("=" * 60)

    pairs = find_pairs()
    if not pairs:
        print("❌ 未找到 md + json 配对文件")
        return

    print(f"找到 {len(pairs)} 个文件配对:")
    for p in pairs:
        print(f"  - {p['slug']}: {p['md_file'].name} + {p['json_file'].name}")

    for pair in pairs:
        try:
            import_paper(pair)
        except Exception as e:
            print(f"  ❌ 导入失败: {e}")

    print(f"\n{'=' * 60}")
    print(f"✅ 导入完成! 共 {len(pairs)} 篇论文")


if __name__ == "__main__":
    main()
