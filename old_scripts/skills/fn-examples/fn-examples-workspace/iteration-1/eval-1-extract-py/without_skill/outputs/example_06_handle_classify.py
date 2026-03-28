"""
example_06_handle_classify.py

Demonstrates: _handle_classify(arguments)

Purpose:
    Processes the raw arguments from the "classify_genes" tool call
    (the 2-step approach, step 1). It:
      1. Extracts paper metadata (Title, Journal, DOI) into an extraction dict
      2. Builds a gene_dict mapping each gene name to its normalized category

    Category normalization via CATEGORY_MAP handles variant labels the AI
    might produce, e.g.:
      "Enzymatic / Biosynthesis" -> "Pathway"
      "Transcription factor / Regulatory" -> "Regulation"
      "enzyme" -> "Pathway"

    If category is unrecognized, defaults to "Common".
"""

import json
from typing import Tuple

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


def _handle_classify(arguments: dict) -> Tuple[dict, dict]:
    """Process classify_genes result -> (extraction_init, gene_dict)."""
    extraction = {
        "Title": arguments.get("Title", "NA"),
        "Journal": arguments.get("Journal", "NA"),
        "DOI": arguments.get("DOI", "NA"),
        "Common_Genes": [],
        "Pathway_Genes": [],
        "Regulation_Genes": [],
    }

    genes_list = arguments.get("genes", [])
    if isinstance(genes_list, str):
        try:
            genes_list = json.loads(genes_list)
        except json.JSONDecodeError:
            genes_list = []

    gene_dict = {}
    for g in genes_list:
        if not isinstance(g, dict):
            continue
        gname = g.get("Gene_Name") or g.get("gene") or g.get("gene_name") or g.get("name") or ""
        cat = g.get("category", "Common")
        cat = CATEGORY_MAP.get(cat, cat)  # Normalize category
        if cat not in ("Common", "Pathway", "Regulation"):
            cat = "Common"
        if gname:
            gene_dict[gname] = cat

    return extraction, gene_dict


# ── Example 1: Standard classification result ────────────────────────────

print("=== Example 1: Standard classify_genes response ===")
classify_response = {
    "Title": "Overexpression of petunia chalcone isomerase in tomato",
    "Journal": "Nature Biotechnology",
    "DOI": "10.1038/nbt0901-470",
    "genes": [
        {"Gene_Name": "CHI", "category": "Pathway", "reason": "Chalcone isomerase enzyme"},
        {"Gene_Name": "CHS", "category": "Pathway", "reason": "Chalcone synthase enzyme"},
        {"Gene_Name": "SlMYB12", "category": "Regulation", "reason": "MYB transcription factor"},
        {"Gene_Name": "PAL", "category": "Common", "reason": "General phenylpropanoid gene"},
    ]
}

extraction, gene_dict = _handle_classify(classify_response)
print(f"Title: {extraction['Title']}")
print(f"gene_dict: {json.dumps(gene_dict, indent=2)}")

# ── Example 2: AI uses non-standard category names ──────────────────────

print("\n=== Example 2: Non-standard category names (auto-normalized) ===")
messy_response = {
    "Title": "Test paper",
    "Journal": "Test",
    "DOI": "NA",
    "genes": [
        {"Gene_Name": "CHS", "category": "Enzymatic / Biosynthesis"},     # -> "Pathway"
        {"Gene_Name": "MYB12", "category": "Transcription factor"},       # -> "Regulation"
        {"Gene_Name": "DFR", "category": "enzyme"},                       # -> "Pathway"
        {"Gene_Name": "XYZ", "category": "Unknown Category"},             # -> "Common" (fallback)
    ]
}

_, gene_dict2 = _handle_classify(messy_response)
print(f"gene_dict: {json.dumps(gene_dict2, indent=2)}")
# Notice how all non-standard categories are properly normalized

# ── Example 3: genes list as JSON string ─────────────────────────────────

print("\n=== Example 3: genes as JSON string (edge case) ===")
string_response = {
    "Title": "Test",
    "Journal": "Test",
    "DOI": "NA",
    "genes": '[{"Gene_Name": "F3H", "category": "Pathway"}]'
}

_, gene_dict3 = _handle_classify(string_response)
print(f"gene_dict: {gene_dict3}")
