"""
_split_sections — Split a markdown document by top-level '# ' headings into
a preamble and a list of (heading, body) tuples.

Source: extractor/text_utils.py:162

Usage:
    python _split_sections.py
"""

# --- External Imports ---
import re


# --- Target Function ---

def _split_sections(md_content):
    """
    按 '# ' 开头的行将 Markdown 拆分为多个 section。

    Returns:
        preamble: 第一个 '# ' 标题之前的内容（通常为空或 metadata）
        sections: list of (heading, body) 元组
                  heading 是 '# ...' 那一行（不含换行符）
                  body 是该标题到下一个 '# ' 标题之间的全部内容
    """
    # 找到所有以 '# ' 开头的行的位置（只匹配一级标题 '# '，不匹配 '## '）
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

        # 提取标题行（第一行）
        newline_pos = chunk.find('\n')
        if newline_pos == -1:
            heading = chunk.strip()
            body = ''
        else:
            heading = chunk[:newline_pos].strip()
            body = chunk[newline_pos:]

        sections.append((heading, body))

    return preamble, sections


# --- Sample Input ---
# A realistic paper-like markdown with preamble metadata, then several
# top-level sections. Note that '## ' sub-headings are NOT split points —
# they remain inside the body of their parent '# ' section.

sample_md = """\
---
doi: 10.1038/nbt.1399
journal: Nature Biotechnology
---

# Enrichment of Tomato Fruit with Anthocyanins

Anthocyanins are water-soluble pigments with antioxidant properties.

## Background

Previous studies showed that dietary anthocyanins extend lifespan in mice.

# Results

Transgenic tomato lines expressing *Del* and *Ros1* accumulated high levels
of anthocyanins in the fruit.

## Anthocyanin Quantification

Total anthocyanin content reached 3 mg/g fresh weight.

# Materials and Methods

Tomato (*Solanum lycopersicum*) cv. MicroTom was used as the parental line.

# References

1. Butelli E et al. (2008) Nat Biotechnol 26: 1301-1308.
2. Martin C et al. (2011) Curr Opin Plant Biol 14: 235-243.
"""

# --- Run ---
if __name__ == "__main__":
    preamble, sections = _split_sections(sample_md)

    print("=== Preamble ===")
    print(repr(preamble) if preamble.strip() else "(empty)")
    print()

    print(f"=== {len(sections)} Sections Found ===")
    for i, (heading, body) in enumerate(sections):
        # Show first 80 chars of body to keep output concise
        body_preview = body.strip()[:80].replace('\n', ' ')
        print(f"  [{i}] Heading: {heading}")
        print(f"       Body preview: {body_preview}...")
        print()

    # Also demonstrate: document with no headings
    plain_text = "This document has no top-level headings at all.\nJust plain text."
    preamble2, sections2 = _split_sections(plain_text)
    print("=== No headings case ===")
    print(f"  preamble = {preamble2!r}")
    print(f"  sections = {sections2}")
