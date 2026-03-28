"""
_handle_extract — Process extract_*_genes function-call result into a gene array.

Parses the 'genes' field from an OpenAI tool-call argument dict, handling cases
where the value might be a JSON string instead of a list.

Source: extractor/extract.py:279

Usage:
    python _handle_extract.py
"""

import json

# --- Target Function ---

def _handle_extract(arguments: dict, arr_key: str) -> list:
    """Process extract_*_genes result -> gene array."""
    genes_arr = arguments.get("genes", [])
    if isinstance(genes_arr, str):
        try:
            genes_arr = json.loads(genes_arr)
        except json.JSONDecodeError:
            genes_arr = []
    return genes_arr if isinstance(genes_arr, list) else []

# --- Sample Input ---

# Case 1: Normal list of gene dicts (typical successful response)
arguments_normal = {
    "genes": [
        {
            "Gene_Name": "SlCHI1",
            "Species": "tomato",
            "Pathway": "flavonoid biosynthesis",
            "Phenotype_Direction": "increase",
            "Target_Nutrient": "flavonols",
        },
        {
            "Gene_Name": "SlF3H",
            "Species": "tomato",
            "Pathway": "flavonoid biosynthesis",
            "Phenotype_Direction": "increase",
            "Target_Nutrient": "kaempferol",
        },
    ]
}

# Case 2: Genes as a JSON string (some LLMs return stringified JSON)
arguments_string = {
    "genes": '[{"Gene_Name": "OsNAS2", "Species": "rice", "Target_Nutrient": "iron"}]'
}

# Case 3: Empty / missing genes key
arguments_empty = {}

# --- Run ---
if __name__ == "__main__":
    print("=== Case 1: Normal list ===")
    result1 = _handle_extract(arguments_normal, "Common_Genes")
    print(json.dumps(result1, indent=2, ensure_ascii=False))

    print("\n=== Case 2: JSON string ===")
    result2 = _handle_extract(arguments_string, "Pathway_Genes")
    print(json.dumps(result2, indent=2, ensure_ascii=False))

    print("\n=== Case 3: Empty ===")
    result3 = _handle_extract(arguments_empty, "Regulation_Genes")
    print(f"Result: {result3}")
