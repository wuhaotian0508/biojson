#!/usr/bin/env python3
"""
Example: _split_sections()

Splits a Markdown document into sections based on level-1 headings ('# ').
Returns a preamble (text before the first heading) and a list of
(heading, body) tuples.

Note: Only matches '# ' (level 1), not '## ' (level 2).

Signature:
    _split_sections(md_content: str) -> tuple[str, list[tuple[str, str]]]
"""
import sys, os
sys.path.insert(0, '/data/haotianwu/biojson')

from extractor.text_utils import _split_sections

# ── Example 1: Typical paper with multiple sections ──────────────────────────
paper = """\
Some metadata or title area before headings.

# Introduction

This paper studies carotenoid biosynthesis in tomato.

# Results

## Overexpression of OsCHI

OsCHI overexpression led to 3x increase in flavonols.

## Metabolite Analysis

HPLC analysis confirmed the changes.

# Methods

Plants were grown under controlled conditions.

# References

1. Smith et al. (2020)
"""

preamble, sections = _split_sections(paper)

print("=== Example 1: Typical paper ===")
print(f"Preamble: {repr(preamble.strip())}")
print(f"Number of sections: {len(sections)}")
print()
for i, (heading, body) in enumerate(sections):
    body_preview = body.strip()[:80] + "..." if len(body.strip()) > 80 else body.strip()
    print(f"  Section {i}: heading={repr(heading)}")
    print(f"             body preview={repr(body_preview)}")
print()

# ── Example 2: No headings at all ───────────────────────────────────────────
text_no_headings = "Just a plain text document with no markdown headings."
preamble2, sections2 = _split_sections(text_no_headings)

print("=== Example 2: No headings ===")
print(f"Preamble: {repr(preamble2)}")
print(f"Sections: {sections2}")
assert sections2 == [], "Should have no sections"
print("PASS: returns full text as preamble, empty sections list")
print()

# ── Example 3: Only level-2 headings (not matched) ──────────────────────────
text_h2_only = """\
## Introduction

Some intro.

## Methods

Some methods.
"""

preamble3, sections3 = _split_sections(text_h2_only)

print("=== Example 3: Only ## headings (not split) ===")
print(f"Preamble: {repr(preamble3.strip()[:60])}...")
print(f"Sections: {sections3}")
assert sections3 == [], "Level-2 headings should not cause splits"
print("PASS: ## headings are not treated as section boundaries")
print()

# ── Example 4: Heading with no body ─────────────────────────────────────────
text_empty_body = """\
# Title Only
# Next Section

Content here.
"""

preamble4, sections4 = _split_sections(text_empty_body)

print("=== Example 4: Heading with empty body ===")
print(f"Number of sections: {len(sections4)}")
for i, (heading, body) in enumerate(sections4):
    print(f"  Section {i}: heading={repr(heading)}, body={repr(body.strip())}")
print("PASS: handles headings with no body text")
