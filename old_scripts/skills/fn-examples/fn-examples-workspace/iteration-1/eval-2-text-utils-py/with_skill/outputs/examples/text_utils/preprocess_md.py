"""
preprocess_md — One-stop markdown preprocessing entry point that strips images,
URLs, extra blank lines, and irrelevant sections from MinerU-converted papers.

Source: extractor/text_utils.py:27

NOTE: This example uses a mock for the LLM call (used internally by
extract_relevant_sections) so it runs without API credentials.

Usage:
    python preprocess_md.py
"""

# --- External Imports ---
import re
import os
import json
from unittest.mock import MagicMock, patch


# --- Inlined Dependencies ---
# (all copied from extractor/text_utils.py, in dependency order)

def strip_images(md_content):
    """(Inlined from text_utils.py:53) Remove markdown image tags."""
    return re.sub(r'!\[[^\]]*\]\([^)]*\)', '', md_content)


def strip_urls(md_content):
    """(Inlined from text_utils.py:67) Remove parenthesized URLs."""
    return re.sub(r'\(https?://[^)]*\)', '', md_content)


def strip_extra_blanks(md_content):
    """(Inlined from text_utils.py:153) Collapse 3+ blank lines to 2."""
    return re.sub(r'\n{3,}', '\n\n', md_content)


def _split_sections(md_content):
    """(Inlined from text_utils.py:162) Split markdown by '# ' headings."""
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


def _classify_headings_with_llm(headings):
    """(Inlined from text_utils.py:201) Call LLM to classify headings."""
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
    )
    model = os.getenv("MODEL", "Vendor2/Claude-4.6-opus")

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

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that identifies irrelevant sections in scientific papers. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=200,
        )
        answer = response.choices[0].message.content.strip()

        json_match = re.search(r'\[[\d\s,]*\]', answer)
        if json_match:
            indices = json.loads(json_match.group())
            return set(int(i) for i in indices if 0 <= i < len(headings))
        else:
            print(f"    [text_utils] LLM returned unparseable result: {answer}")
            return None

    except Exception as e:
        print(f"    [text_utils] LLM section classification call failed: {e}")
        return None


def extract_relevant_sections(md_content):
    """(Inlined from text_utils.py:272) Filter out irrelevant sections using LLM."""
    preamble, sections = _split_sections(md_content)

    if not sections:
        return md_content

    headings = [h for h, _ in sections]
    print(f"    [text_utils] Found {len(headings)} section headings, calling LLM to classify...")

    remove_indices = _classify_headings_with_llm(headings)

    if remove_indices is None:
        print(f"    [text_utils] LLM call failed, using full text (fallback)")
        return md_content

    for i, h in enumerate(headings):
        mark = "REMOVE" if i in remove_indices else "KEEP  "
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
    print(f"    [text_utils] Removed {removed_count} sections, kept {kept_count}")
    print(f"    [text_utils] Text from {orig_len} -> {kept_len} chars "
          f"(kept {kept_len * 100 // max(orig_len, 1)}%)")

    return result


# --- Target Function ---

def preprocess_md(md_content):
    """
    一站式 Markdown 预处理：去除 MinerU 转换产生的所有无用内容。

    调用方只需：
        from text_utils import preprocess_md
        content = preprocess_md(raw_md)

    Args:
        md_content: MinerU 转换后的 Markdown 全文

    Returns:
        清理后的文本（图片、引用列表、致谢 已去除，多余空行已合并，
        且只保留 Results + Materials & Methods 相关 section）
    """
    content = strip_images(md_content)
    content = strip_urls(content)
    content = strip_extra_blanks(content)
    content = extract_relevant_sections(content)
    return content


# --- Mock Setup ---

def _create_mock_response(removed_indices):
    """Build a mock OpenAI ChatCompletion response."""
    mock_message = MagicMock()
    mock_message.content = json.dumps(removed_indices)
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


# --- Sample Input ---
# A realistic MinerU-converted paper fragment that includes all the artifacts
# that preprocess_md is designed to remove: images (CDN + local), URLs,
# excessive blank lines, and irrelevant sections (Introduction, References,
# Acknowledgments).

sample_md = """\
---
doi: 10.1038/nbt0901-834
journal: Nature Biotechnology
---

# Overexpression of Petunia Chalcone Isomerase in Tomato

![Banner](https://cdn-mineru.openxlab.org.cn/result/abcdef/banner.png)

Flavonols are bioactive polyphenols with antioxidant properties.

# Introduction

Tomato fruit naturally contains low levels of flavonols (https://www.plantcell.org/about).
Previous work showed that the flavonoid pathway is present but poorly expressed in fruit peel.




# Results

![](images/fig1_pathway.png)

Expression of petunia *CHI* in tomato increased fruit peel flavonol content by 78-fold.

## Flavonol Quantification

Quercetin rutinoside levels reached 60 ug/g fresh weight in transgenic fruit
(https://doi.org/10.1038/nbt0901-834), compared to 0.8 ug/g in wild-type.




## Carotenoid and Ascorbate Levels

Neither carotenoid nor ascorbate levels were significantly affected.

# Materials and Methods

Tomato (*Solanum lycopersicum*) cv. FM6203 was transformed with a construct
containing petunia *CHI-A* cDNA under the CaMV 35S promoter.

# References

1. Muir SR et al. (2001) Overexpression of petunia chalcone isomerase. Nat Biotechnol 19: 470-474.
2. Colliver S et al. (2002) Improving the nutritional content of tomato fruit. J Exp Bot 53: 2099-2106.

# Acknowledgments

We thank Dr. S. Colliver for help with HPLC analysis and BBSRC for funding.
"""


# --- Run ---
if __name__ == "__main__":
    print(f"=== Original: {len(sample_md)} chars ===")
    print(sample_md[:300] + "...")
    print()

    # Mock LLM to remove indices 1 (Introduction), 4 (References), 5 (Acknowledgments)
    mock_removed = [1, 4, 5]
    mock_response = _create_mock_response(mock_removed)

    with patch("openai.OpenAI") as MockOpenAI:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        MockOpenAI.return_value = mock_client

        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-mock-key",
            "OPENAI_BASE_URL": "https://mock.api.example.com/v1",
            "MODEL": "mock-model",
        }):
            result = preprocess_md(sample_md)

    print()
    print(f"=== Preprocessed: {len(result)} chars ===")
    print(result)
