"""
_handle_extract_all — Process the extract_all_genes function-call result into
an extraction dict and a gene_dict mapping gene names to their categories.

Source: extractor/extract.py:189

Usage:
    python _handle_extract_all.py
"""

import json
from typing import Tuple

# --- Target Function ---

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

# --- Sample Input ---
# Simulates what the LLM returns when it calls the extract_all_genes tool.
# This is a realistic response from a paper about carotenoid biosynthesis in tomato.
arguments = {
    "Title": "Multi-level engineering facilitates the production of phenylpropanoid compounds in tomato",
    "Journal": "Nature Communications",
    "DOI": "10.1038/s41467-015-3298-7",
    "Common_Genes": [
        {
            "Gene_Name": "SlGAD2",
            "Species": "tomato",
            "Pathway": "GABA shunt",
            "Target_Nutrient": "GABA",
            "Phenotype_Direction": "increase",
            "Evidence_Type": "genetic perturbation",
        },
    ],
    "Pathway_Genes": [
        {
            "Gene_Name": "SlCHI1",
            "Species": "tomato",
            "Pathway": "flavonoid biosynthesis",
            "Target_Nutrient": "flavonols",
            "Phenotype_Direction": "increase",
            "Evidence_Type": "enzyme assay",
        },
        {
            "Gene_Name": "SlF3H",
            "Species": "tomato",
            "Pathway": "flavonoid biosynthesis",
            "Target_Nutrient": "kaempferol glycosides",
            "Phenotype_Direction": "increase",
            "Evidence_Type": "genetic perturbation",
        },
    ],
    "Regulation_Genes": [
        {
            "Gene_Name": "SlMYB12",
            "Species": "tomato",
            "Pathway": "flavonoid regulatory",
            "Target_Nutrient": "total phenylpropanoids",
            "Phenotype_Direction": "increase",
            "Evidence_Type": "overexpression + metabolite profiling",
        },
    ],
}

# --- Run ---
if __name__ == "__main__":
    extraction, gene_dict = _handle_extract_all(arguments)

    print("=== Extraction Dict ===")
    print(json.dumps(extraction, indent=2, ensure_ascii=False))

    print("\n=== Gene Dict (name -> category) ===")
    print(json.dumps(gene_dict, indent=2, ensure_ascii=False))
