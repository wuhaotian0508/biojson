"""
extract_relevant_sections — Remove irrelevant paper sections (Introduction,
References, Acknowledgments, etc.) by splitting on '# ' headings, calling
an LLM to classify them, and reassembling only the relevant parts.

Source: extractor/text_utils.py:272

NOTE: This example uses a mock for the LLM call so it runs without API
credentials. The mock simulates the LLM marking Introduction, References,
and Acknowledgments for removal.

Usage:
    python extract_relevant_sections.py
"""

# --- External Imports ---
import re
import os
import json
from unittest.mock import MagicMock, patch


# --- Inlined Dependencies ---
# (copied from extractor/text_utils.py)

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
    """(Inlined from text_utils.py:201) Call LLM to classify headings for removal."""
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


# --- Target Function ---

def extract_relevant_sections(md_content):
    """
    去除论文中不相关的 section（Introduction、References、Acknowledgments 等），
    保留其余所有内容。

    流程：
        1. 按 '# ' 拆分所有 section
        2. 收集所有标题，一次性调用 LLM 判断哪些需要去除
        3. 拼接：preamble + 未被去除的 section
        4. 如果 LLM 调用失败，返回原始全文（fallback）

    Args:
        md_content: 经过基础清洗后的 Markdown 文本

    Returns:
        去除无关 section 后的文本
    """
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
# A complete paper-like markdown document with 6 sections.
# The mock LLM will mark indices 1, 4, 5 (Introduction, References,
# Acknowledgments) for removal.

sample_md = """\
---
doi: 10.1038/nbt.1399
---

# Enrichment of Tomato Fruit with Anthocyanins

Anthocyanins are potent dietary antioxidants found in many fruits.

# Introduction

Tomato (*Solanum lycopersicum*) is the second most consumed vegetable crop
worldwide, but its fruit lacks significant anthocyanin accumulation.

# Results

Expression of *Delila* (Del) and *Rosea1* (Ros1) from snapdragon under the
fruit-specific E8 promoter resulted in high anthocyanin accumulation.

## Anthocyanin Analysis

Total anthocyanin content in transgenic fruit reached 3.0 mg/g FW compared
to trace amounts in wild-type fruit.

# Materials and Methods

Tomato cv. MicroTom was transformed via Agrobacterium-mediated transformation.

# References

1. Butelli E et al. (2008) Enrichment of tomato fruit with health-promoting
   anthocyanins. Nat Biotechnol 26: 1301-1308.
2. Martin C et al. (2013) Purple tomatoes. Curr Biol 23: R520-R521.

# Acknowledgments

We thank the John Innes Centre for greenhouse facilities.
"""

# --- Run ---
if __name__ == "__main__":
    # Indices the mock LLM says to remove: Introduction, References, Acknowledgments
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
            result = extract_relevant_sections(sample_md)

    print()
    print("=== Filtered Output ===")
    print(result)
