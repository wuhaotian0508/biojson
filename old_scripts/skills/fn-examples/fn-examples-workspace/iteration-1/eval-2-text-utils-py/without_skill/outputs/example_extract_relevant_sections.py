#!/usr/bin/env python3
"""
Example: extract_relevant_sections()

Removes irrelevant sections (Introduction, References, Acknowledgments, etc.)
from a paper by:
  1. Splitting on '# ' headings via _split_sections()
  2. Calling LLM to classify which headings to remove
  3. Reassembling only the kept sections

Falls back to the full original text if the LLM call fails.

Since this requires a live LLM API, the example mocks _classify_headings_with_llm.

Signature:
    extract_relevant_sections(md_content: str) -> str
"""
import sys, os
sys.path.insert(0, '/data/haotianwu/biojson')

from unittest.mock import patch

# ── Example 1: Typical paper -- remove Introduction and References ───────────
paper = """\
Paper Title and Abstract area.

# Introduction

Background on flavonoid metabolism.

# Results

OsCHI overexpression led to 3x increase in flavonol content.

# Methods

Tomato plants were grown in a greenhouse.

# References

1. Smith et al. (2020) Nature 580, 1-10.

# Acknowledgments

We thank Dr. Jones for seeds.
"""

# Mock: remove indices 0 (Introduction), 3 (References), 4 (Acknowledgments)
def mock_classify_1(headings):
    return {0, 3, 4}

print("=== Example 1: Remove Introduction, References, Acknowledgments ===")
with patch("extractor.text_utils._classify_headings_with_llm", side_effect=mock_classify_1):
    from extractor.text_utils import extract_relevant_sections
    result1 = extract_relevant_sections(paper)

print(result1)
print("---")
assert "# Introduction" not in result1, "Introduction should be removed"
assert "# References" not in result1, "References should be removed"
assert "# Acknowledgments" not in result1, "Acknowledgments should be removed"
assert "# Results" in result1, "Results should be kept"
assert "# Methods" in result1, "Methods should be kept"
print("PASS: correct sections removed/kept")
print()

# ── Example 2: LLM fails -- fallback to full text ───────────────────────────
def mock_classify_fail(headings):
    return None  # Simulates LLM failure

print("=== Example 2: LLM failure fallback ===")
with patch("extractor.text_utils._classify_headings_with_llm", side_effect=mock_classify_fail):
    result2 = extract_relevant_sections(paper)

assert result2 == paper, "On LLM failure, should return original text"
print("PASS: returns original text on LLM failure")
print()

# ── Example 3: No headings at all ───────────────────────────────────────────
plain_text = "This is just a plain paragraph with no headings."

print("=== Example 3: No headings (returned as-is) ===")
with patch("extractor.text_utils._classify_headings_with_llm") as mock_llm:
    result3 = extract_relevant_sections(plain_text)
    mock_llm.assert_not_called()  # LLM should not be called when there are no headings

assert result3 == plain_text
print("PASS: returned as-is, LLM not called")
print()

# ── Example 4: Nothing removed ──────────────────────────────────────────────
small_paper = """\
# Results

Key findings here.

# Methods

Experimental procedures.
"""

def mock_classify_none_removed(headings):
    return set()  # Nothing to remove

print("=== Example 4: Nothing removed ===")
with patch("extractor.text_utils._classify_headings_with_llm", side_effect=mock_classify_none_removed):
    result4 = extract_relevant_sections(small_paper)

assert "# Results" in result4
assert "# Methods" in result4
print("PASS: all sections kept when LLM says nothing to remove")
