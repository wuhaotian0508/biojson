"""
example_16_category_map.py

Demonstrates: CATEGORY_MAP and CAT_TO_TOOL constants

Purpose:
    CATEGORY_MAP normalizes the various category labels that the AI might
    produce into the three canonical categories: Common, Pathway, Regulation.

    The AI sometimes returns verbose or inconsistent category names like:
      "Enzymatic / Biosynthesis", "transcription factor", "enzyme", etc.
    CATEGORY_MAP maps all variants to the canonical form.

    CAT_TO_TOOL maps each canonical category to the corresponding
    extraction tool name, used in the 2-step approach to decide which
    tool to invoke for detailed extraction.
"""

CATEGORY_MAP = {
    "Enzymatic / Biosynthesis": "Pathway",
    "Transcription factor / Regulatory": "Regulation",
    "Transcription Factor / Regulatory": "Regulation",
    "enzymatic / biosynthesis": "Pathway",
    "transcription factor / regulatory": "Regulation",
    "Enzymatic": "Pathway",
    "Biosynthesis": "Pathway",
    "Transcription factor": "Regulation",
    "Regulatory": "Regulation",
    "biosynthesis": "Pathway",
    "regulatory": "Regulation",
    "transcription factor": "Regulation",
    "enzyme": "Pathway",
    "Enzyme": "Pathway",
}

CAT_TO_TOOL = {
    "Common":     "extract_common_genes",
    "Pathway":    "extract_pathway_genes",
    "Regulation": "extract_regulation_genes",
}


# ── Example 1: Normalize various AI-produced category labels ─────────────

print("=== CATEGORY_MAP: Normalize category labels ===")
test_labels = [
    "Common",                          # Already canonical -> stays
    "Pathway",                         # Already canonical -> stays
    "Regulation",                      # Already canonical -> stays
    "Enzymatic / Biosynthesis",        # -> Pathway
    "Transcription factor / Regulatory", # -> Regulation
    "enzyme",                          # -> Pathway
    "biosynthesis",                    # -> Pathway
    "transcription factor",            # -> Regulation
    "Regulatory",                      # -> Regulation
    "Unknown",                         # Not in map -> stays as-is
]

for label in test_labels:
    normalized = CATEGORY_MAP.get(label, label)
    changed = " (normalized)" if normalized != label else ""
    print(f"  '{label}' -> '{normalized}'{changed}")

# ── Example 2: Map canonical categories to tool names ────────────────────

print("\n=== CAT_TO_TOOL: Category -> extraction tool ===")
for cat, tool in CAT_TO_TOOL.items():
    print(f"  {cat:12s} -> {tool}")

# ── Example 3: Real usage pattern ────────────────────────────────────────

print("\n=== Real usage: normalize then pick tool ===")
genes_from_ai = [
    {"Gene_Name": "CHS", "category": "Enzymatic / Biosynthesis"},
    {"Gene_Name": "SlMYB12", "category": "Transcription factor"},
    {"Gene_Name": "PAL", "category": "Common"},
]

for g in genes_from_ai:
    raw_cat = g["category"]
    normalized = CATEGORY_MAP.get(raw_cat, raw_cat)
    if normalized not in ("Common", "Pathway", "Regulation"):
        normalized = "Common"  # fallback
    tool = CAT_TO_TOOL[normalized]
    print(f"  {g['Gene_Name']:10s}  '{raw_cat}' -> '{normalized}' -> {tool}")
