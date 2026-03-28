#!/usr/bin/env python3
"""
Example: strip_acknowledgments()

Removes the Acknowledgments section from a paper.
Handles both American ("Acknowledgments") and British ("Acknowledgements") spelling.
If another heading follows, it and everything after are preserved.

Signature:
    strip_acknowledgments(md_content: str) -> str
"""
import sys, os
sys.path.insert(0, '/data/haotianwu/biojson')

from extractor.text_utils import strip_acknowledgments

# ── Example 1: Acknowledgments at the end ────────────────────────────────────
text1 = """\
# Results

Gene expression was significantly increased.

# Acknowledgments

We thank Dr. Smith for providing seeds. This work was supported by NIH grant R01.
"""

result1 = strip_acknowledgments(text1)
print("=== Example 1: Acknowledgments at end ===")
print(result1)
print("---")
print()

# ── Example 2: Acknowledgments followed by References ────────────────────────
text2 = """\
# Methods

PCR was performed using standard protocols.

# Acknowledgments

Funded by NSF grant 12345.

# References

1. Smith et al. (2020)
"""

result2 = strip_acknowledgments(text2)
print("=== Example 2: Acknowledgments before References ===")
print(result2)
print("---")
print()

# ── Example 3: British spelling "Acknowledgements" ──────────────────────────
text3 = """\
# Discussion

SlMYB12 plays a key regulatory role.

## Acknowledgements

The authors wish to thank the reviewers.
"""

result3 = strip_acknowledgments(text3)
print("=== Example 3: British spelling (Acknowledgements) ===")
print(result3)
print("---")
print()

# ── Example 4: ALL CAPS variant ─────────────────────────────────────────────
text4 = """\
# Results

Data shown in Figure 1.

# ACKNOWLEDGMENTS

We thank all collaborators.
"""

result4 = strip_acknowledgments(text4)
print("=== Example 4: ALL CAPS variant ===")
print(result4)
print("---")
print()

# ── Example 5: No acknowledgments (no-op) ───────────────────────────────────
text5 = "# Results\n\nSome findings.\n\n# Methods\n\nSome methods.\n"
result5 = strip_acknowledgments(text5)
print("=== Example 5: No acknowledgments (unchanged) ===")
assert result5 == text5, "Text without acknowledgments should be unchanged"
print("PASS: text unchanged when no acknowledgments present")
