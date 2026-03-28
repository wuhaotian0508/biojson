"""
rollback.py
回退已处理的文件：删除对应的 JSON 输出，将 MD 从 processed 移回 md/。

用法（通过 run.sh 调用）:
    bash scripts/run.sh rollback plcell          # 模糊匹配
    bash scripts/run.sh rollback plcell.md       # 带 .md 后缀也行
    bash scripts/run.sh rollback MinerU_markdown_plcell_v31_5_937_2031566954798968832  # 完整文件名

回退操作:
    1. 删除 json/{stem}_nutri_plant_verified.json
    2. 删除 reports/{dirname}/extraction.json
    3. 删除 reports/{dirname}/verification.json
    4. 如果 reports 子目录变空则删除目录
    5. 将 md/processed/{name}.md 移回 md/{name}.md
"""

import os
import sys
import shutil

# ─── 路径配置 ────────────────────────────────────────────────
BASE_DIR = os.getenv("BASE_DIR", "/data/haotianwu/biojson")
MD_DIR = os.getenv("MD_DIR", os.path.join(BASE_DIR, "md"))
PROCESSED_DIR = os.getenv("PROCESSED_DIR", os.path.join(MD_DIR, "processed"))
JSON_DIR = os.getenv("JSON_DIR", os.path.join(BASE_DIR, "json"))
REPORTS_DIR = os.getenv("REPORTS_DIR", os.path.join(BASE_DIR, "reports"))


def stem_to_dirname(stem):
    """将 MD 文件名 stem 转为 reports 子目录名（与 md_to_json.py / verify_response.py 保持一致）。"""
    if stem.startswith("MinerU_markdown_"):
        stem = stem[len("MinerU_markdown_"):]
    stem = stem.replace("_(1)", "")
    stem = stem.replace("_", "-")
    return stem


def find_matching_files(keyword):
    """在 md/processed/ 中查找匹配的文件。

    匹配规则（全部大小写不敏感）：
      1. 精确匹配（含/不含 .md 后缀）
      2. 关键词包含在文件名中（去掉 MinerU_markdown_ 前缀后也尝试匹配）
    """
    if not os.path.exists(PROCESSED_DIR):
        return []

    processed_files = sorted([f for f in os.listdir(PROCESSED_DIR) if f.endswith(".md")])
    if not processed_files:
        return []

    # 标准化关键词
    kw = keyword.lower()
    if kw.endswith(".md"):
        kw = kw[:-3]

    matches = []
    for f in processed_files:
        fname_lower = f.lower()
        stem_lower = fname_lower[:-3]  # 去掉 .md

        # 精确匹配（完整 stem 或去掉 MinerU_markdown_ 前缀后的 stem）
        stem_no_prefix = stem_lower
        if stem_no_prefix.startswith("mineru_markdown_"):
            stem_no_prefix = stem_no_prefix[len("mineru_markdown_"):]

        if kw == stem_lower or kw == stem_no_prefix:
            # 精确匹配优先级最高，直接返回
            return [f]

        # 模糊匹配：关键词包含在文件名中（含/不含前缀）
        if kw in stem_lower or kw in stem_no_prefix:
            matches.append(f)

    return matches


def rollback_file(md_filename):
    """回退单个文件，返回操作是否成功。"""
    stem = os.path.splitext(md_filename)[0]
    dirname = stem_to_dirname(stem)

    print(f"\n{'─'*50}")
    print(f"🔄 回退: {md_filename}")
    print(f"{'─'*50}")

    success = True

    # 1. 删除 json/{stem}_nutri_plant_verified.json
    verified_json = os.path.join(JSON_DIR, f"{stem}_nutri_plant_verified.json")
    if os.path.exists(verified_json):
        os.remove(verified_json)
        print(f"  🗑️  已删除: {verified_json}")
    else:
        print(f"  ⏭️  不存在（跳过）: {verified_json}")

    # 2. 删除 reports/{dirname}/verification.json
    report_dir = os.path.join(REPORTS_DIR, dirname)
    verification_json = os.path.join(report_dir, "verification.json")
    if os.path.exists(verification_json):
        os.remove(verification_json)
        print(f"  🗑️  已删除: {verification_json}")
    else:
        print(f"  ⏭️  不存在（跳过）: {verification_json}")

    # 3. 删除 reports/{dirname}/extraction.json
    extraction_json = os.path.join(report_dir, "extraction.json")
    if os.path.exists(extraction_json):
        os.remove(extraction_json)
        print(f"  🗑️  已删除: {extraction_json}")
    else:
        print(f"  ⏭️  不存在（跳过）: {extraction_json}")

    # 4. 删除 reports/{dirname}/extraction-error.json（如果有）
    extraction_error = os.path.join(report_dir, "extraction-error.json")
    if os.path.exists(extraction_error):
        os.remove(extraction_error)
        print(f"  🗑️  已删除: {extraction_error}")

    # 5. 如果 reports 子目录为空则删除
    if os.path.exists(report_dir) and not os.listdir(report_dir):
        os.rmdir(report_dir)
        print(f"  🗑️  已删除空目录: {report_dir}")

    # 6. 将 MD 从 processed 移回 md/
    src = os.path.join(PROCESSED_DIR, md_filename)
    dst = os.path.join(MD_DIR, md_filename)
    if os.path.exists(src):
        if os.path.exists(dst):
            print(f"  ⚠️  目标已存在: {dst}，覆盖")
        shutil.move(src, dst)
        print(f"  📦 已移回: {dst}")
    else:
        print(f"  ❌ MD 文件不存在: {src}")
        success = False

    return success


def main():
    keyword = os.getenv("ROLLBACK_TARGET", "")
    if not keyword:
        print("❌ 请指定要回退的文件名关键词")
        print("   用法: bash scripts/run.sh rollback <文件名关键词>")
        print("")
        print("   示例:")
        print("     bash scripts/run.sh rollback plcell")
        print("     bash scripts/run.sh rollback plcell.md")
        print("     bash scripts/run.sh rollback MinerU_markdown_plcell_v31_5_937_2031566954798968832")
        sys.exit(1)

    # 列出 processed 中的文件供参考
    if os.path.exists(PROCESSED_DIR):
        processed = sorted([f for f in os.listdir(PROCESSED_DIR) if f.endswith(".md")])
    else:
        processed = []

    if not processed:
        print("❌ md/processed/ 目录为空，没有可回退的文件")
        sys.exit(1)

    print(f"📂 已处理文件 ({len(processed)} 个):")
    for f in processed:
        print(f"   - {f}")
    print()

    # 查找匹配
    matches = find_matching_files(keyword)

    if not matches:
        print(f"❌ 未找到匹配 '{keyword}' 的文件")
        print(f"   提示: 关键词会在文件名中进行模糊匹配（不区分大小写，无需 MinerU_markdown_ 前缀或 .md 后缀）")
        sys.exit(1)

    if len(matches) > 1:
        print(f"⚠️  匹配到 {len(matches)} 个文件，请使用更精确的关键词:")
        for f in matches:
            print(f"   - {f}")
        sys.exit(1)

    # 唯一匹配，执行回退
    target = matches[0]
    print(f"🎯 匹配到: {target}")

    ok = rollback_file(target)

    if ok:
        print(f"\n✅ 回退完成！文件已移回 md/ 目录，可以重新处理。")
    else:
        print(f"\n⚠️  回退过程中有部分操作失败，请检查上方日志。")


if __name__ == "__main__":
    main()
