"""
check_sections.py
扫描所有 MD 文件，列出每篇论文的 section 结构，
特别标注 References 之后还有哪些 section（如 STAR Methods、Plant materials 等）。
"""

import os
import re

MD_DIR = "/data/haotianwu/biojson/md"

# 匹配 Markdown 标题（# / ## / ###）
HEADING_PATTERN = re.compile(r'^(#{1,3})\s+(.+)$', re.MULTILINE)

# 判断一个 section 是否"有用"（对基因提取有价值）
USEFUL_KEYWORDS = [
    r'method', r'star\s*method', r'experimental\s*procedure',
    r'plant\s*material', r'growth\s*condition', r'transgenic',
    r'accession\s*number', r'key\s*resources?\s*table',
    r'method\s*detail', r'quantification', r'statistical',
    r'data\s*and\s*code', r'data\s*availability',
    r'resource\s*availability', r'cloning', r'genotyp',
    r'phenotyp', r'metabol', r'hplc', r'lc-ms', r'gc-ms',
    r'rna.?seq', r'expression\s*analysis', r'supplemental?\s*method',
    r'experimental\s*model', r'reagent',
]

# 判断一个 section 是否"无用"
USELESS_KEYWORDS = [
    r'references?\s*(and\s*notes)?$', r'acknowledg', r'author\s*contribut',
    r'competing\s*interest', r'conflict\s*of\s*interest',
    r'supplemental?\s*(information|data|figure|table)(?!\s*method)',
    r'supplementary\s*(information|figure\s*legend)',
    r'abbreviation',
]


def classify_heading(title):
    """分类标题：useful / useless / unknown"""
    title_lower = title.strip().lower()
    for kw in USEFUL_KEYWORDS:
        if re.search(kw, title_lower):
            return "✅ 有用"
    for kw in USELESS_KEYWORDS:
        if re.search(kw, title_lower):
            return "❌ 无用"
    return "❓ 未知"


def analyze_file(filepath):
    """分析单个 MD 文件的 section 结构"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    filename = os.path.basename(filepath)
    total_chars = len(content)

    # 找到所有标题
    headings = []
    for match in HEADING_PATTERN.finditer(content):
        level = len(match.group(1))
        title = match.group(2).strip()
        pos = match.start()
        headings.append((level, title, pos))

    # 找到 References 的位置
    ref_idx = None
    for i, (level, title, pos) in enumerate(headings):
        if re.search(r'(?i)^references?\s*(and\s*notes)?$', title):
            ref_idx = i
            break

    return {
        "filename": filename,
        "total_chars": total_chars,
        "headings": headings,
        "ref_idx": ref_idx,
    }


def main():
    files = sorted([f for f in os.listdir(MD_DIR) if f.endswith('.md')])

    print(f"{'═' * 80}")
    print(f"📄 扫描 {len(files)} 篇论文的 Section 结构")
    print(f"{'═' * 80}")

    for filepath in files:
        info = analyze_file(os.path.join(MD_DIR, filepath))
        headings = info["headings"]
        ref_idx = info["ref_idx"]

        print(f"\n{'─' * 80}")
        print(f"📄 {info['filename']}  ({info['total_chars']:,} 字符)")
        print(f"{'─' * 80}")

        if ref_idx is None:
            print(f"  ⚠️  未找到 References section")
            # 显示所有一级标题
            print(f"  所有一级标题:")
            for level, title, pos in headings:
                if level == 1:
                    pct = pos / info['total_chars'] * 100
                    print(f"    [{pct:5.1f}%] # {title}")
            continue

        ref_level, ref_title, ref_pos = headings[ref_idx]
        ref_pct = ref_pos / info['total_chars'] * 100
        chars_before_ref = ref_pos
        chars_after_ref = info['total_chars'] - ref_pos

        print(f"  📍 References 位置: 字符 {ref_pos:,} / {info['total_chars']:,} ({ref_pct:.1f}%)")
        print(f"  📏 References 之前: {chars_before_ref:,} 字符")
        print(f"  📏 References 及之后: {chars_after_ref:,} 字符 ({chars_after_ref/info['total_chars']*100:.1f}%)")

        # References 之后的 section
        after_ref = headings[ref_idx + 1:] if ref_idx + 1 < len(headings) else []

        if not after_ref:
            print(f"  ✅ References 之后没有其他 section（可以直接砍掉）")
        else:
            print(f"\n  📋 References 之后的 section ({len(after_ref)} 个):")
            has_useful = False
            for level, title, pos in after_ref:
                pct = pos / info['total_chars'] * 100
                classification = classify_heading(title)
                prefix = "#" * level
                print(f"    [{pct:5.1f}%] {classification}  {prefix} {title}")
                if "有用" in classification:
                    has_useful = True

            if has_useful:
                print(f"\n  ⚠️  References 后面有有用的 section！不能简单全部砍掉。")
            else:
                print(f"\n  ✅ References 后面没有有用的 section，可以安全砍掉。")

    # 汇总建议
    print(f"\n{'═' * 80}")
    print(f"📊 汇总建议")
    print(f"{'═' * 80}")
    print(f"  策略：去掉 References 引用列表，但保留后面有用的 Methods 类 section")
    print(f"  具体做法：")
    print(f"    1. 找到 References 标题位置")
    print(f"    2. 找到 References 之后的下一个「有用」section")
    print(f"    3. 删除 References 标题 到 有用 section 之间的内容（引用列表 + 致谢等）")
    print(f"    4. 保留有用 section 及其内容")


if __name__ == "__main__":
    main()
