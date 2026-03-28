#!/usr/bin/env python3
"""
Example: strip_urls()

Removes parenthesized HTTP/HTTPS URLs from text.
These are common in MinerU-converted papers and waste tokens.

Signature:
    strip_urls(md_content: str) -> str
"""
import sys, os
sys.path.insert(0, '/data/haotianwu/biojson')

from extractor.text_utils import strip_urls

# ── Example 1: NCBI GEO link ────────────────────────────────────────────────
text1 = "Data are available at GEO (https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE147589) under accession GSE147589."
result1 = strip_urls(text1)
print("=== Example 1: NCBI GEO link ===")
print(f"Before: {text1}")
print(f"After:  {result1}")
print()

# ── Example 2: DOI link ─────────────────────────────────────────────────────
text2 = "See the dataset (https://doi.org/10.5281/zenodo.5237316) for details."
result2 = strip_urls(text2)
print("=== Example 2: DOI link ===")
print(f"Before: {text2}")
print(f"After:  {result2}")
print()

# ── Example 3: Multiple URLs in one paragraph ───────────────────────────────
text3 = """\
Tools used include BLAST (https://blast.ncbi.nlm.nih.gov/) and \
Clustal Omega (https://www.ebi.ac.uk/Tools/msa/clustalo/). \
See also (http://www.plantcell.org) for the journal."""

result3 = strip_urls(text3)
print("=== Example 3: Multiple URLs ===")
print(f"Before: {text3}")
print(f"After:  {result3}")
print()

# ── Example 4: Non-URL parentheses are preserved ────────────────────────────
text4 = "The gene (OsCHI) was found in rice (Oryza sativa L.)."
result4 = strip_urls(text4)
print("=== Example 4: Non-URL parentheses preserved ===")
print(f"Before: {text4}")
print(f"After:  {result4}")
assert result4 == text4, "Non-URL parentheses should be unchanged"
print("PASS: non-URL parentheses unchanged")
