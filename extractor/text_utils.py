"""
text_utils.py — Text preprocessing for the extractor pipeline.

Removes images, URLs, and irrelevant sections from paper Markdown
to reduce token consumption before LLM calls.

Public API:
    preprocess_md()         — local-only text cleaning (no LLM calls)
    preprocess_md_for_llm() — cleaning + LLM-based section filtering
"""

import re
import json


# ═══════════════════════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════════════════════

def preprocess_md(md_content):
    """Local text preprocessing: no remote calls.

    Args:
        md_content: raw Markdown from MinerU conversion

    Returns:
        Cleaned text (images/URLs removed, extra blanks collapsed)
    """
    content = strip_images(md_content)
    content = strip_urls(content)
    content = strip_extra_blanks(content)
    return content


def preprocess_md_for_llm(md_content, tracker=None):
    """Preprocessing for extraction/verification, includes LLM section filtering."""
    content = preprocess_md(md_content)
    return extract_relevant_sections(content, tracker=tracker)


# ═══════════════════════════════════════════════════════════════════════════════
#  Text cleaning functions
# ═══════════════════════════════════════════════════════════════════════════════

def strip_images(md_content):
    """Remove Markdown image tags (both CDN and local path formats)."""
    return re.sub(r'!\[[^\]]*\]\([^)]*\)', '', md_content)


def strip_urls(md_content):
    """Remove parenthesized URLs: (https://...) or (http://...)."""
    return re.sub(r'\(https?://[^)]*\)', '', md_content)


def strip_extra_blanks(md_content):
    """Collapse 3+ consecutive blank lines to 2."""
    return re.sub(r'\n{3,}', '\n\n', md_content)


# ═══════════════════════════════════════════════════════════════════════════════
#  Section filtering: keep Results + Materials & Methods via LLM classification
# ═══════════════════════════════════════════════════════════════════════════════

def _split_sections(md_content):
    """Split Markdown into sections by '# ' headings.

    Returns:
        preamble: content before the first '# ' heading
        sections: list of (heading, body) tuples
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
    """Call LLM to identify which headings should be removed.

    Uses the shared client/fallback from config. Optionally tracks token usage.

    Args:
        headings: list of str, all '# ' headings in the paper
        tracker: optional TokenTracker instance

    Returns:
        set of int (indices to remove), or None on failure
    """
    from .config import get_openai_client, get_fallback_client, MODEL, FALLBACK_MODEL

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
        return _try_call(get_openai_client(), MODEL)
    except Exception as e:
        print(f"    ⚠️  [text_utils] Primary LLM section 分类失败: {e}")

    fallback_client = get_fallback_client()
    if fallback_client and FALLBACK_MODEL:
        try:
            print(f"    🔄 [text_utils] Switching to Fallback ({FALLBACK_MODEL})...")
            return _try_call(fallback_client, FALLBACK_MODEL)
        except Exception as e:
            print(f"    ❌ [text_utils] Fallback LLM section 分类也失败: {e}")

    return None


def extract_relevant_sections(md_content, tracker=None):
    """Remove irrelevant sections (Intro, References, Acknowledgments, etc.).

    Flow:
        1. Split all sections by '# '
        2. Call LLM once to classify which headings to remove
        3. Reassemble: preamble + kept sections
        4. Falls back to full text if LLM call fails
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
