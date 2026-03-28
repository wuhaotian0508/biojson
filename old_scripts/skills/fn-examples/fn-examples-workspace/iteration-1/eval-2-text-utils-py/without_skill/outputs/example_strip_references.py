#!/usr/bin/env python3
"""
Example: strip_references()

Removes the References / Literature Cited section from a paper.
If another heading follows after the references, that heading and
everything after it is preserved.

Signature:
    strip_references(md_content: str) -> str
"""
import sys, os
sys.path.insert(0, '/data/haotianwu/biojson')

from extractor.text_utils import strip_references

# ── Example 1: References at the end (nothing after) ─────────────────────────
text1 = """\
# Results

Gene X was overexpressed and led to 3x increase in lycopene.

# References

1. Smith et al. (2020) Nature 580, 1-10.
2. Jones et al. (2019) Science 365, 50-55.
3. Wang et al. (2018) Plant Cell 30, 100-115.
"""

result1 = strip_references(text1)
print("=== Example 1: References at end (truncated) ===")
print(result1)
print("---")
print()

# ── Example 2: References followed by another section ────────────────────────
text2 = """\
# Results

Important findings about carotenoid biosynthesis.

# References

1. Smith et al. (2020) Nature 580, 1-10.
2. Jones et al. (2019) Science 365, 50-55.

# Supplementary Materials

Table S1 shows additional data.
"""

result2 = strip_references(text2)
print("=== Example 2: References with content after ===")
print(result2)
print("---")
print()

# ── Example 3: "Literature Cited" variant ────────────────────────────────────
text3 = """\
# Discussion

Our study demonstrates the role of SlMYB12.

## Literature Cited

Brown, J. (2021). Plant Biology...
"""

result3 = strip_references(text3)
print("=== Example 3: 'Literature Cited' variant ===")
print(result3)
print("---")
print()

# ── Example 4: "References and Notes" variant ────────────────────────────────
text4 = """\
# Methods

Standard PCR protocols were used.

# References and Notes

1. See supplementary materials.
"""

result4 = strip_references(text4)
print("=== Example 4: 'References and Notes' variant ===")
print(result4)
print("---")
print()

# ── Example 5: No references section (no-op) ────────────────────────────────
text5 = """\
# Results

Some results here.

# Methods

Some methods here.
"""

result5 = strip_references(text5)
print("=== Example 5: No references (unchanged) ===")
assert result5 == text5, "Text without references should be unchanged"
print("PASS: text unchanged when no references present")
