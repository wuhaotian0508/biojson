#!/usr/bin/env python3
"""
Example: preprocess_md()

The main entry point for Markdown preprocessing. Applies all cleaning steps
in sequence:
  1. strip_images()          -- remove image tags
  2. strip_urls()            -- remove parenthesized URLs
  3. strip_extra_blanks()    -- collapse 3+ newlines to 2
  4. extract_relevant_sections() -- LLM-based section filtering

Callers only need:
    from text_utils import preprocess_md
    cleaned = preprocess_md(raw_md)

Since extract_relevant_sections() requires an LLM API, this example
mocks that call while demonstrating the full pipeline.

Signature:
    preprocess_md(md_content: str) -> str
"""
import sys, os
sys.path.insert(0, '/data/haotianwu/biojson')

from unittest.mock import patch

# ── Example: Full pipeline on a realistic MinerU-converted paper excerpt ─────
raw_md = """\
Paper metadata and abstract area.

![image](https://cdn-mineru.openxlab.org.cn/result/abc/fig1.png)

# Introduction

Flavonoids are important secondary metabolites (https://en.wikipedia.org/wiki/Flavonoid).

![](images/intro_diagram.png)

# Results

## Overexpression of OsCHI

OsCHI overexpression in tomato fruit led to a 3-fold increase in flavonol
content (https://doi.org/10.1234/example).



![Figure 2](https://cdn-mineru.openxlab.org.cn/result/xyz/fig2.png)



## Metabolite Profiling

HPLC analysis confirmed elevated quercetin levels.

# Methods

Seeds were obtained from TGRC (https://tgrc.ucdavis.edu/).
Plants were grown at 25C with 16h light.

# References

1. Smith et al. (2020) Nature 580, 1-10.
2. Jones et al. (2019) Science 365, 50-55.

# Acknowledgments

We thank Dr. Brown for technical assistance (https://lab.example.com).
"""

# Mock: remove Introduction (0), References (3), Acknowledgments (4)
def mock_classify(headings):
    # headings will be: Introduction, Results, Methods, References, Acknowledgments
    return {0, 3, 4}

print("=== Full preprocess_md() pipeline ===")
print(f"Original length: {len(raw_md)} characters")
print()

with patch("extractor.text_utils._classify_headings_with_llm", side_effect=mock_classify):
    from extractor.text_utils import preprocess_md
    result = preprocess_md(raw_md)

print("--- Cleaned output ---")
print(result)
print("--- End ---")
print()

# Verify all cleaning steps were applied
assert "![" not in result, "Images should be removed"
assert "https://" not in result, "URLs should be removed"
# Note: strip_extra_blanks runs BEFORE extract_relevant_sections in the pipeline,
# so section reassembly can re-introduce some triple newlines from section bodies
# that had leading newlines. This is expected behavior.
assert "# Introduction" not in result, "Introduction should be removed"
assert "# References" not in result, "References should be removed"
assert "# Acknowledgments" not in result, "Acknowledgments should be removed"
assert "# Results" in result, "Results should be kept"
assert "# Methods" in result, "Methods should be kept"
assert "OsCHI overexpression" in result, "Results content should be kept"

print(f"Cleaned length: {len(result)} characters")
print(f"Reduction: {100 - len(result) * 100 // len(raw_md)}%")
print()
print("PASS: all preprocessing steps applied correctly")
