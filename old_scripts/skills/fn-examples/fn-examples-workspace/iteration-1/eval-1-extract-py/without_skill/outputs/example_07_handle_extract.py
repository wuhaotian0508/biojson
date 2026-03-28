"""
example_07_handle_extract.py

Demonstrates: _handle_extract(arguments, arr_key)

Purpose:
    Processes the result of extract_common_genes / extract_pathway_genes /
    extract_regulation_genes tool calls (used in the legacy 2-step approach,
    step 2).

    It simply extracts the "genes" array from the tool call arguments,
    handling the case where it might be a JSON string or not a list.

    Returns: a list of gene dicts, or empty list on failure.

    Note: arr_key parameter exists in the signature but is not used in the
    function body -- it was kept for interface consistency.
"""

import json


def _handle_extract(arguments: dict, arr_key: str) -> list:
    """Process extract_*_genes result -> gene array."""
    genes_arr = arguments.get("genes", [])
    if isinstance(genes_arr, str):
        try:
            genes_arr = json.loads(genes_arr)
        except json.JSONDecodeError:
            genes_arr = []
    return genes_arr if isinstance(genes_arr, list) else []


# ── Example 1: Normal response ───────────────────────────────────────────

print("=== Example 1: Normal gene extraction ===")
pathway_result = {
    "genes": [
        {
            "Gene_Name": "CHS",
            "Enzyme_Name": "Chalcone synthase",
            "Substrate": "4-coumaroyl-CoA + 3 malonyl-CoA",
            "Product": "Naringenin chalcone",
            "Species": "Solanum lycopersicum"
        },
        {
            "Gene_Name": "CHI",
            "Enzyme_Name": "Chalcone isomerase",
            "Substrate": "Naringenin chalcone",
            "Product": "Naringenin",
            "Species": "Petunia hybrida"
        }
    ]
}

genes = _handle_extract(pathway_result, "Pathway_Genes")
print(f"Extracted {len(genes)} pathway genes:")
for g in genes:
    print(f"  - {g['Gene_Name']}: {g['Enzyme_Name']}")

# ── Example 2: Genes as JSON string ──────────────────────────────────────

print("\n=== Example 2: Genes as JSON string ===")
string_result = {
    "genes": '[{"Gene_Name": "FLS", "Enzyme_Name": "Flavonol synthase"}]'
}

genes2 = _handle_extract(string_result, "Pathway_Genes")
print(f"Parsed from string: {genes2}")

# ── Example 3: Missing or invalid genes ──────────────────────────────────

print("\n=== Example 3: Edge cases ===")
print(f"Empty dict:    {_handle_extract({}, 'x')}")
print(f"No genes key:  {_handle_extract({'other': 'data'}, 'x')}")
print(f"Invalid JSON:  {_handle_extract({'genes': 'not valid json {'}, 'x')}")
print(f"Not a list:    {_handle_extract({'genes': 42}, 'x')}")
