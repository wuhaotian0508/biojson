"""
text_utils.py — Text preprocessing for the extractor pipeline.

Removes images, URLs, and irrelevant sections from paper Markdown
to reduce token consumption before LLM calls.

Public API:
    preprocess_md()         — local-only text cleaning (no LLM calls)
    preprocess_md_for_llm() — cleaning + LLM-based section filtering

[PR 改动 by 学长 muskliu - 2026-03-29]
- 拆分入口函数为两层：preprocess_md()（纯本地清洗）和 preprocess_md_for_llm()（含 LLM section 过滤）
  原来 preprocess_md() 里直接调了 extract_relevant_sections（会发 LLM 请求），
  现在拆开后方便测试和复用本地清洗逻辑
- 删除 strip_references() 和 strip_acknowledgments() 函数（~100 行）
  这两个功能已被 LLM section 过滤取代，不再需要正则匹配
- 删除未使用的 import os
- docstring 从中文改为英文
- extract_relevant_sections() 新增 tracker 参数，支持 token 用量追踪
"""

import re
import json


# ═══════════════════════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════════════════════

def preprocess_md(md_content):
    """纯本地文本清洗，不调用任何远程 API。

    [PR 改动] 原来的 preprocess_md() 内部直接调了 extract_relevant_sections()（会发 LLM 请求），
    现在拆成两层：preprocess_md() 只做本地清洗，preprocess_md_for_llm() 才加 LLM 过滤。
    这样方便测试、RAG 等场景复用纯本地清洗逻辑。

    步骤：去图片标签 → 去 URL → 合并多余空行

    Args:
        md_content: MinerU 转换后的 Markdown 原始文本

    Returns:
        清洗后的文本
    """
    content = strip_images(md_content)
    content = strip_urls(content)
    content = strip_extra_blanks(content)
    return content


def preprocess_md_for_llm(md_content, tracker=None):
    """用于提取/验证的完整预处理：本地清洗 + LLM section 过滤。

    [PR 新增函数] 在 preprocess_md() 基础上，额外调用 LLM 判断各 section 标题，
    去掉 Introduction/References/Acknowledgments 等无关内容，只保留 Results + Methods。

    Args:
        md_content: Markdown 原始文本
        tracker: 可选的 TokenTracker，用于追踪 LLM section 分类的 token 用量
    """
    content = preprocess_md(md_content)
    return extract_relevant_sections(content, tracker=tracker)


# ═══════════════════════════════════════════════════════════════════════════════
#  Text cleaning functions
# ═══════════════════════════════════════════════════════════════════════════════

def strip_images(md_content):
    """去除 Markdown 图片标签（CDN 和本地路径两种格式）。

    例: ![alt](https://cdn.com/img.png) → 删除
    """
    return re.sub(r'!\[[^\]]*\]\([^)]*\)', '', md_content)


def strip_urls(md_content):
    """去除括号内的 URL 链接。

    例: (https://doi.org/10.1234) → 删除
    """
    return re.sub(r'\(https?://[^)]*\)', '', md_content)


def strip_extra_blanks(md_content):
    """合并多余空行：3个以上连续空行 → 2个。"""
    return re.sub(r'\n{3,}', '\n\n', md_content)


# ═══════════════════════════════════════════════════════════════════════════════
#  Section filtering: keep Results + Materials & Methods via LLM classification
# ═══════════════════════════════════════════════════════════════════════════════

def _split_sections(md_content):
    """按一级标题（# ）把 Markdown 拆分为多个 section。

    Returns:
        preamble: 第一个 # 标题之前的内容（通常是论文标题/摘要）
        sections: [(标题, 正文), ...] 列表
    """
    heading_pattern = re.compile(r'^# ', re.MULTILINE)
    matches = list(heading_pattern.finditer(md_content))

    if not matches:
        return md_content, []

    preamble = md_content[:matches[0].start()]
    sections = []

    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md_content)
        chunk = md_content[start:end]

        newline_pos = chunk.find('\n')
        if newline_pos == -1:
            heading = chunk.strip()
            body = ''
        else:
            heading = chunk[:newline_pos].strip()
            body = chunk[newline_pos:]

        sections.append((heading, body))

    return preamble, sections


def _classify_headings_with_llm(headings, tracker=None):
    """调用 LLM 判断哪些 section 标题应该被移除。

    给 LLM 发一个编号标题列表，让它返回要移除的编号（JSON 数组）。
    调用 extraction API；失败时返回 None，由上层使用原文继续处理。

    [PR 改动] 新增 tracker 参数，支持追踪 section 分类这一步的 token 用量。

    Args:
        headings: 所有 # 标题的列表
        tracker: 可选的 TokenTracker

    Returns:
        set[int]: 要移除的标题索引集合，LLM 调用失败返回 None
    """
    from .config import get_openai_client, EXTRACTOR_MODEL

    heading_list = "\n".join(f"{i}: {h}" for i, h in enumerate(headings))

    prompt = f"""Below is a numbered list of section headings from a scientific paper.
Please identify which headings should be REMOVED because they are NOT relevant to experimental results or methods.

Remove these types of sections:
- Introduction / Background
- References / References and Notes / Literature Cited
- Acknowledgments / Acknowledgements
- Author Contributions / Authors Contributions
- Funding / Financial Support
- Competing Interests / Conflict of Interest
- Additional Information
- Resource Distribution

Keep everything else (including Results, Methods, Discussion, paper title sections with content, Supplementary Materials, Accession Numbers etc.)

Headings:
{heading_list}

Return ONLY a JSON array of the index numbers that should be REMOVED.
Example: [0, 2, 4]
If nothing should be removed, return: []"""

    messages = [
        {"role": "system", "content": "You are a helpful assistant that identifies irrelevant sections in scientific papers. Return only valid JSON."},
        {"role": "user", "content": prompt},
    ]

    def _try_call(client, model):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
            max_tokens=200,
        )
        if tracker:
            tracker.add(response, stage="preprocess", file="section_filter")
        answer = response.choices[0].message.content.strip()
        json_match = re.search(r'\[[\d\s,]*\]', answer)
        if json_match:
            indices = json.loads(json_match.group())
            return set(int(i) for i in indices if 0 <= i < len(headings))
        print(f"    ⚠️  [text_utils] LLM 返回无法解析的结果: {answer}")
        return None

    try:
        return _try_call(get_openai_client(), EXTRACTOR_MODEL)
    except Exception as e:
        print(f"    ⚠️  [text_utils] LLM section 分类失败: {e}")

    return None


def extract_relevant_sections(md_content, tracker=None):
    """去除无关 section（Introduction/References/Acknowledgments 等）。

    [PR 改动] 新增 tracker 参数。

    流程：
    1. 按 # 标题拆分所有 section
    2. 调用一次 LLM 分类哪些标题要移除
    3. 重新拼接：preamble + 保留的 section
    4. LLM 调用失败则 fallback 使用全文
    """
    preamble, sections = _split_sections(md_content)

    if not sections:
        return md_content

    headings = [h for h, _ in sections]
    print(f"    📑 [text_utils] 发现 {len(headings)} 个 section 标题，调用 LLM 分类...")

    remove_indices = _classify_headings_with_llm(headings, tracker=tracker)

    if remove_indices is None:
        print(f"    ⚠️  [text_utils] LLM 调用失败，使用全文 (fallback)")
        return md_content

    for i, h in enumerate(headings):
        mark = "❌ 去除" if i in remove_indices else "✅ 保留"
        print(f"        {mark}  {h}")

    parts = [preamble.rstrip()]
    for i, (heading, body) in enumerate(sections):
        if i not in remove_indices:
            parts.append(heading + body)

    result = "\n\n".join(p for p in parts if p.strip())

    kept_len = len(result)
    orig_len = len(md_content)
    removed_count = len(remove_indices)
    kept_count = len(sections) - removed_count
    print(f"    📊 [text_utils] 去除 {removed_count} 个 section，保留 {kept_count} 个")
    print(f"    📊 [text_utils] 文本从 {orig_len} → {kept_len} 字符 "
          f"(保留 {kept_len * 100 // max(orig_len, 1)}%)")

    return result
