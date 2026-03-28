"""
_schema_props_to_fc — Convert a gene type's properties dict to OpenAI function-calling compatible format.

Source: extractor/extract.py:36

Usage:
    python _schema_props_to_fc.py
"""

import json

# --- Target Function ---

def _schema_props_to_fc(gene_def: dict) -> dict:
    """Convert a gene type's properties to FC-compatible format."""
    fc_props = {}
    for field_name, field_schema in gene_def.get("properties", {}).items():
        desc = field_schema.get("description", "")
        fc_props[field_name] = {"type": "string", "description": desc}
    return fc_props

# --- Sample Input ---
# A gene type definition from the extraction schema.
# "properties" maps field names to their schema (description, type, default).
# This represents part of a CommonGene definition with fields typical of
# crop nutrient metabolism gene annotation.
gene_def = {
    "properties": {
        "Gene_Name": {
            "title": "Gene_Name",
            "description": "The name or symbol of the Core Gene, e.g., TaGS5, Pi2.",
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": "NA",
        },
        "Species": {
            "title": "Species",
            "description": "The main species studied (common name), e.g., rice, tomato.",
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": "NA",
        },
        "Pathway": {
            "title": "Pathway",
            "description": "The metabolic or signaling pathway the gene participates in.",
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": "NA",
        },
        "Phenotype_Direction": {
            "title": "Phenotype_Direction",
            "description": "Whether the gene increases or decreases the target nutrient.",
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": "NA",
        },
    }
}

# --- Run ---
if __name__ == "__main__":
    result = _schema_props_to_fc(gene_def)
    print("=== Result ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
