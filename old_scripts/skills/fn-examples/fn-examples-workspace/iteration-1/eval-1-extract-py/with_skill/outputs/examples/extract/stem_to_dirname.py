"""
stem_to_dirname — Convert a markdown file stem to a report directory name.

Strips the 'MinerU_markdown_' prefix, removes '_(1)' suffixes, and replaces
underscores with hyphens. Used to create clean, filesystem-friendly directory
names for extraction report output.

Source: extractor/extract.py:337

Usage:
    python stem_to_dirname.py
"""

# --- Target Function ---

def stem_to_dirname(stem: str) -> str:
    if stem.startswith("MinerU_markdown_"):
        stem = stem[len("MinerU_markdown_"):]
    stem = stem.replace("_(1)", "")
    stem = stem.replace("_", "-")
    return stem

# --- Sample Input ---
# Various paper file stems in the formats encountered in the pipeline.

test_cases = [
    # Standard MinerU-converted paper (prefix stripped, underscores to hyphens)
    "MinerU_markdown_NBT-biosynthesis-Overexpression_of_petunia_2034201331278598144",
    # Duplicate file with _(1) suffix (suffix removed)
    "MinerU_markdown_s41586-022-04950-4_(1)_2031567254796566528",
    # Short-form paper name (no MinerU prefix)
    "Mol_Plant_2016_Yang",
    # Paper with simple name
    "Nat_Biotechnol_2008_Butelli",
]

# --- Run ---
if __name__ == "__main__":
    for stem in test_cases:
        result = stem_to_dirname(stem)
        print(f"  {stem}")
        print(f"  -> {result}")
        print()
