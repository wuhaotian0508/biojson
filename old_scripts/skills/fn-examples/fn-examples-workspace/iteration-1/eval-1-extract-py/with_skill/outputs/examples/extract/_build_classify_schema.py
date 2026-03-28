"""
_build_classify_schema — Build the classify_genes OpenAI function-calling schema (inline, no file reference).

Source: extractor/extract.py:74

Usage:
    python _build_classify_schema.py
"""

import json

# --- Target Function ---

def _build_classify_schema() -> dict:
    """Build the classify_genes FC schema (inline, no file reference)."""
    return {
        "type": "function",
        "function": {
            "name": "classify_genes",
            "description": (
                "Identify ALL core genes from the paper's Results section and classify each into "
                "one of three categories: Common / Pathway / Regulation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "Title": {"type": "string", "description": "Full paper title."},
                    "Journal": {"type": "string", "description": "Journal name."},
                    "DOI": {"type": "string", "description": "Pure DOI string, no URL prefix."},
                    "genes": {
                        "type": "array",
                        "description": "List of all core genes identified from the paper.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "Gene_Name": {"type": "string", "description": "Gene name or symbol."},
                                "category": {
                                    "type": "string",
                                    "enum": ["Common", "Pathway", "Regulation"],
                                    "description": "Gene category.",
                                },
                                "reason": {"type": "string", "description": "Brief reason for classification."},
                            },
                            "required": ["Gene_Name", "category"],
                        },
                    },
                },
                "required": ["Title", "Journal", "DOI", "genes"],
            },
        },
    }

# --- Sample Input ---
# This function takes no arguments. It builds and returns a fixed schema
# used for the gene classification step of the extraction pipeline.

# --- Run ---
if __name__ == "__main__":
    result = _build_classify_schema()
    print("=== classify_genes FC schema ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
