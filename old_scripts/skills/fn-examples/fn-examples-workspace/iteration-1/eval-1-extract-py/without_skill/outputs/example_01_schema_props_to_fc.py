"""
example_01_schema_props_to_fc.py

Demonstrates: _schema_props_to_fc(gene_def)

Purpose:
    Converts a gene type definition (from JSON Schema) into a simplified
    format suitable for OpenAI function calling. It flattens all property
    types to "string" and preserves descriptions.

    Input:  A dict with a "properties" key containing field definitions
    Output: A dict where every field is {"type": "string", "description": ...}
"""

import json


def _schema_props_to_fc(gene_def: dict) -> dict:
    """Convert a gene type's properties to FC-compatible format."""
    fc_props = {}
    for field_name, field_schema in gene_def.get("properties", {}).items():
        desc = field_schema.get("description", "")
        fc_props[field_name] = {"type": "string", "description": desc}
    return fc_props


# ── Example: a realistic gene type definition (subset of fields) ──────────

gene_def = {
    "properties": {
        "Gene_Name": {
            "type": "string",
            "description": "Official gene symbol, e.g. SlMYB12"
        },
        "Species": {
            "type": ["string", "null"],
            "description": "Species name where the gene was studied"
        },
        "Pathway": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Metabolic pathway(s) the gene is involved in"
        },
        "Phenotype_Direction": {
            "type": "string",
            "enum": ["increase", "decrease", "no change"],
            "description": "Direction of phenotype change when gene is perturbed"
        }
    }
}

result = _schema_props_to_fc(gene_def)
print("Input gene_def properties:")
for name, schema in gene_def["properties"].items():
    print(f"  {name}: type={schema.get('type')}")

print("\nOutput FC-compatible properties:")
print(json.dumps(result, indent=2))

# Notice: all types become "string" regardless of original type.
# This is because OpenAI function calling works best with string types
# and lets the model fill in the value as a string.

print("\n--- Edge case: empty properties ---")
empty_def = {"properties": {}}
print(f"Empty: {_schema_props_to_fc(empty_def)}")

print("\n--- Edge case: missing 'properties' key ---")
no_props = {"other_key": "value"}
print(f"No properties key: {_schema_props_to_fc(no_props)}")
