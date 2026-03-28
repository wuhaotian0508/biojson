"""
example_10_stem_to_dirname.py

Demonstrates: stem_to_dirname(stem)

Purpose:
    Converts a markdown file stem (filename without extension) into a
    clean directory name for storing extraction reports.

    Transformations:
      1. Strips "MinerU_markdown_" prefix (artifact from MinerU conversion tool)
      2. Removes "_(1)" suffix (duplicate file markers)
      3. Replaces all underscores with hyphens

    This ensures consistent directory naming in the reports/ folder.
"""


def stem_to_dirname(stem: str) -> str:
    if stem.startswith("MinerU_markdown_"):
        stem = stem[len("MinerU_markdown_"):]
    stem = stem.replace("_(1)", "")
    stem = stem.replace("_", "-")
    return stem


# ── Example 1: Standard paper filename ───────────────────────────────────

print("=== Standard paper filenames ===")
examples = [
    "Mol_Plant_2016_Yang",
    "Nat_Biotechnol_2008_Butelli",
    "Science_2003_Xie",
    "PNAS_2024_Peng",
    "Plant_Biotechnol_J_2026_Yang",
]

for stem in examples:
    dirname = stem_to_dirname(stem)
    print(f"  {stem:40s} -> {dirname}")

# ── Example 2: MinerU prefix files ──────────────────────────────────────

print("\n=== MinerU prefix files ===")
mineru_examples = [
    "MinerU_markdown_NBT-biosynthesis-Overexpression_2034201331278598144",
    "MinerU_markdown_plcell_v31_5_937_2031566954798968832",
    "MinerU_markdown_tieman2017_2031567451551371264",
]

for stem in mineru_examples:
    dirname = stem_to_dirname(stem)
    print(f"  {stem}")
    print(f"    -> {dirname}")

# ── Example 3: Duplicate file marker ────────────────────────────────────

print("\n=== Files with _(1) duplicate marker ===")
dup_examples = [
    "MinerU_markdown_s41586-022-04950-4_(1)_2031567254796566528",
    "full_(1)",
]

for stem in dup_examples:
    dirname = stem_to_dirname(stem)
    print(f"  {stem}")
    print(f"    -> {dirname}")
