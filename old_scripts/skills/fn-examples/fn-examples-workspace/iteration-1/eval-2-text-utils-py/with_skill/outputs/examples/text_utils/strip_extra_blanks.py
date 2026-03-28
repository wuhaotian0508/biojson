"""
strip_extra_blanks — Collapse runs of 3+ consecutive blank lines down to 2 blank lines.

Source: extractor/text_utils.py:153

Usage:
    python strip_extra_blanks.py
"""

# --- External Imports ---
import re


# --- Target Function ---

def strip_extra_blanks(md_content):
    """合并 3 个以上连续空行为 2 个空行。"""
    return re.sub(r'\n{3,}', '\n\n', md_content)


# --- Sample Input ---
# After stripping images and URLs from a MinerU-converted paper, the text
# often contains large gaps of blank lines where figures used to be.
# This sample simulates that situation with 5 blank lines after a figure
# was removed and 4 blank lines between paragraphs.

sample_md = (
    "# Results\n"
    "\n"
    "Overexpression of *PSY1* increased total carotenoid content by 2.8-fold.\n"
    "\n\n\n\n\n"  # 5 blank lines (where an image was stripped)
    "Table 1 shows the carotenoid composition of transgenic vs. wild-type fruit.\n"
    "\n\n\n\n"    # 4 blank lines (where another image was stripped)
    "## Lycopene Quantification\n"
    "\n"
    "Lycopene levels were measured by HPLC at 472 nm.\n"
)

# --- Run ---
if __name__ == "__main__":
    print("=== Original (repr to show blank lines) ===")
    for i, line in enumerate(sample_md.split('\n')):
        print(f"  {i:2d}: {line!r}")
    print()

    result = strip_extra_blanks(sample_md)

    print("=== After strip_extra_blanks (repr) ===")
    for i, line in enumerate(result.split('\n')):
        print(f"  {i:2d}: {line!r}")
    print()

    print("=== Rendered Output ===")
    print(result)
