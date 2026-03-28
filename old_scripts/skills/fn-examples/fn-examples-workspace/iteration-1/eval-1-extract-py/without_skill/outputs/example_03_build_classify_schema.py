"""
example_03_build_classify_schema.py

Demonstrates: _build_classify_schema()

Purpose:
    Builds the OpenAI function calling schema for the "classify_genes" tool.
    This tool asks the AI to:
      1. Extract paper metadata (Title, Journal, DOI)
      2. Identify ALL core genes from the paper
      3. Classify each gene into one of three categories:
         Common / Pathway / Regulation

    Unlike _build_extract_schema, this schema is hardcoded (no external
    schema file needed) because the classification step always has the
    same fixed structure.
"""

import json


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


# ── Run it ────────────────────────────────────────────────────────────────

schema = _build_classify_schema()
print("classify_genes tool schema:")
print(json.dumps(schema, indent=2))

# Example of what the AI might return when calling this tool:
example_tool_call_args = {
    "Title": "SlMYB12 regulates flavonol biosynthesis in tomato fruit",
    "Journal": "Molecular Plant",
    "DOI": "10.1016/j.molp.2016.01.001",
    "genes": [
        {"Gene_Name": "SlMYB12", "category": "Regulation", "reason": "Transcription factor controlling flavonol pathway"},
        {"Gene_Name": "CHS", "category": "Pathway", "reason": "Chalcone synthase, first enzyme in flavonoid biosynthesis"},
        {"Gene_Name": "FLS", "category": "Pathway", "reason": "Flavonol synthase, produces flavonols from dihydroflavonols"},
    ]
}

print("\nExample tool call arguments (what the AI would produce):")
print(json.dumps(example_tool_call_args, indent=2))
