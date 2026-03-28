"""
example_05_handle_extract_all.py

Demonstrates: _handle_extract_all(arguments)

Purpose:
    Processes the raw arguments returned by the "extract_all_genes" tool call.
    It does two things:
      1. Builds the extraction dict (Title, Journal, DOI + three gene arrays)
      2. Builds a gene_dict mapping Gene_Name -> category ("Common"/"Pathway"/"Regulation")

    Also handles edge cases:
      - genes_arr might be a JSON string instead of a list (parses it)
      - genes_arr might not be a list at all (defaults to empty)
      - Gene name might be in different keys (Gene_Name, gene, gene_name, name)
"""

import json
from typing import Tuple


def _handle_extract_all(arguments: dict) -> Tuple[dict, dict]:
    """Process extract_all_genes result -> (extraction_dict, gene_dict)."""
    extraction = {
        "Title": arguments.get("Title", "NA"),
        "Journal": arguments.get("Journal", "NA"),
        "DOI": arguments.get("DOI", "NA"),
        "Common_Genes": [],
        "Pathway_Genes": [],
        "Regulation_Genes": [],
    }

    gene_dict = {}
    for arr_key, cat in [("Common_Genes", "Common"), ("Pathway_Genes", "Pathway"), ("Regulation_Genes", "Regulation")]:
        genes_arr = arguments.get(arr_key, [])
        if isinstance(genes_arr, str):
            try:
                genes_arr = json.loads(genes_arr)
            except json.JSONDecodeError:
                genes_arr = []
        if not isinstance(genes_arr, list):
            genes_arr = []
        extraction[arr_key] = genes_arr
        for g in genes_arr:
            if isinstance(g, dict):
                gname = g.get("Gene_Name") or g.get("gene") or g.get("gene_name") or g.get("name") or ""
                if gname:
                    gene_dict[gname] = cat

    return extraction, gene_dict


# ── Example 1: Normal case with properly structured data ─────────────────

print("=== Example 1: Normal API response ===")
api_response = {
    "Title": "Metabolic engineering of anthocyanin biosynthesis in tomato",
    "Journal": "Nature Biotechnology",
    "DOI": "10.1038/nbt1260",
    "Common_Genes": [
        {"Gene_Name": "PAL", "Species": "Solanum lycopersicum", "Function_Summary": "Phenylalanine ammonia lyase"}
    ],
    "Pathway_Genes": [
        {"Gene_Name": "CHS", "Enzyme_Name": "Chalcone synthase", "Substrate": "4-coumaroyl-CoA"},
        {"Gene_Name": "CHI", "Enzyme_Name": "Chalcone isomerase", "Substrate": "Naringenin chalcone"}
    ],
    "Regulation_Genes": [
        {"Gene_Name": "Del", "Regulation_Type": "Transcription factor", "Target_Genes": "CHS, CHI, F3H"},
        {"Gene_Name": "Ros1", "Regulation_Type": "Transcription factor", "Target_Genes": "DFR, ANS"}
    ]
}

extraction, gene_dict = _handle_extract_all(api_response)
print(f"Title: {extraction['Title']}")
print(f"Common: {len(extraction['Common_Genes'])} genes")
print(f"Pathway: {len(extraction['Pathway_Genes'])} genes")
print(f"Regulation: {len(extraction['Regulation_Genes'])} genes")
print(f"gene_dict: {json.dumps(gene_dict, indent=2)}")
# gene_dict maps each gene name to its category for quick lookup

# ── Example 2: Gene array is a JSON string (edge case from some APIs) ────

print("\n=== Example 2: Gene array as JSON string ===")
api_response_string = {
    "Title": "Some paper",
    "Journal": "Nature",
    "DOI": "10.1234/test",
    "Common_Genes": [],
    "Pathway_Genes": '[{"Gene_Name": "F3H", "Enzyme_Name": "Flavanone 3-hydroxylase"}]',
    "Regulation_Genes": []
}

extraction2, gene_dict2 = _handle_extract_all(api_response_string)
print(f"Pathway genes (parsed from string): {extraction2['Pathway_Genes']}")
print(f"gene_dict: {gene_dict2}")

# ── Example 3: Alternative gene name keys ────────────────────────────────

print("\n=== Example 3: Different gene name keys ===")
api_response_alt = {
    "Title": "Test",
    "Journal": "Test",
    "DOI": "NA",
    "Common_Genes": [{"gene": "PAL"}],         # uses "gene" key instead of "Gene_Name"
    "Pathway_Genes": [{"gene_name": "CHS"}],    # uses "gene_name"
    "Regulation_Genes": [{"name": "MYB12"}]      # uses "name"
}

_, gene_dict3 = _handle_extract_all(api_response_alt)
print(f"gene_dict (all names found): {gene_dict3}")
