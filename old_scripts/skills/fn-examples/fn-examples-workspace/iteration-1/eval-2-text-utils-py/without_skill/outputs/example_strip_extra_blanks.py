#!/usr/bin/env python3
"""
Example: strip_extra_blanks()

Collapses runs of 3 or more consecutive newlines down to exactly 2 newlines
(i.e., at most one blank line between paragraphs).

Signature:
    strip_extra_blanks(md_content: str) -> str
"""
import sys, os
sys.path.insert(0, '/data/haotianwu/biojson')

from extractor.text_utils import strip_extra_blanks

# ── Example 1: Many blank lines collapsed ───────────────────────────────────
text1 = "Paragraph one.\n\n\n\n\nParagraph two.\n\n\n\n\n\nParagraph three."
result1 = strip_extra_blanks(text1)
print("=== Example 1: Multiple blank lines collapsed ===")
print(f"Before (repr): {repr(text1)}")
print(f"After  (repr): {repr(result1)}")
print(f"Before newline counts: {text1.count(chr(10))} newlines total")
print(f"After  newline counts: {result1.count(chr(10))} newlines total")
assert "\n\n\n" not in result1, "Should not have 3+ consecutive newlines"
print("PASS: no runs of 3+ newlines remain")
print()

# ── Example 2: Exactly 2 newlines preserved ─────────────────────────────────
text2 = "Line A.\n\nLine B."
result2 = strip_extra_blanks(text2)
print("=== Example 2: Two newlines (already fine, unchanged) ===")
print(f"Before: {repr(text2)}")
print(f"After:  {repr(result2)}")
assert result2 == text2, "Two newlines should be unchanged"
print("PASS: double newline preserved")
print()

# ── Example 3: Single newlines preserved ─────────────────────────────────────
text3 = "Line 1\nLine 2\nLine 3"
result3 = strip_extra_blanks(text3)
print("=== Example 3: Single newlines (unchanged) ===")
print(f"Before: {repr(text3)}")
print(f"After:  {repr(result3)}")
assert result3 == text3, "Single newlines should be unchanged"
print("PASS: single newlines preserved")
print()

# ── Example 4: Realistic paper excerpt with excessive whitespace ─────────────
text4 = """\
# Results



Gene OsCHI showed 3-fold increased expression.




## Table 1



| Gene | Fold Change |
|------|------------|
| OsCHI | 3.0 |
"""

result4 = strip_extra_blanks(text4)
print("=== Example 4: Realistic paper excerpt ===")
print(result4)
print("---")
assert "\n\n\n" not in result4
print("PASS: all excess blanks collapsed")
