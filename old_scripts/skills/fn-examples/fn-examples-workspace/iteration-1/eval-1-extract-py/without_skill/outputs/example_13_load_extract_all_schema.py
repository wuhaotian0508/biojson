"""
example_13_load_extract_all_schema.py

Demonstrates: _load_extract_all_schema()

Purpose:
    Loads the single "extract_all_genes" schema from the schema JSON file.
    This is the entry point for the single-step extraction approach.

    Internally it:
      1. Reads SCHEMA_PATH (nutri_gene_schema_v4.json)
      2. Passes the data to _build_extract_all_schema()
      3. Returns the ready-to-use OpenAI function calling tool definition

    This example simulates it using an in-memory schema dict.
"""

import json


def _schema_props_to_fc(gene_def: dict) -> dict:
    fc_props = {}
    for field_name, field_schema in gene_def.get("properties", {}).items():
        desc = field_schema.get("description", "")
        fc_props[field_name] = {"type": "string", "description": desc}
    return fc_props


def _build_extract_all_schema(schema_data: dict) -> dict:
    multi = schema_data.get("MultipleGeneExtraction", {})
    defs = multi.get("$defs", {})
    common_props = _schema_props_to_fc(defs.get("CommonGene", {}))
    pathway_props = _schema_props_to_fc(defs.get("PathwayGene", {}))
    regulation_props = _schema_props_to_fc(defs.get("RegulationGene", {}))

    return {
        "type": "function",
        "function": {
            "name": "extract_all_genes",
            "description": "Extract paper metadata and ALL core genes at once.",
            "parameters": {
                "type": "object",
                "properties": {
                    "Title": {"type": "string"},
                    "Journal": {"type": "string"},
                    "DOI": {"type": "string"},
                    "Common_Genes": {"type": "array", "items": {"type": "object", "properties": common_props}},
                    "Pathway_Genes": {"type": "array", "items": {"type": "object", "properties": pathway_props}},
                    "Regulation_Genes": {"type": "array", "items": {"type": "object", "properties": regulation_props}},
                },
                "required": ["Title", "Journal", "DOI", "Common_Genes", "Pathway_Genes", "Regulation_Genes"],
            },
        },
    }


def _load_extract_all_schema(schema_data: dict) -> dict:
    """Simulated version (real one reads from SCHEMA_PATH file)."""
    return _build_extract_all_schema(schema_data)


# ── Example ──────────────────────────────────────────────────────────────

schema_data = {
    "MultipleGeneExtraction": {
        "$defs": {
            "CommonGene": {
                "properties": {
                    "Gene_Name": {"type": "string", "description": "Gene symbol"},
                    "Species": {"type": "string", "description": "Species"},
                }
            },
            "PathwayGene": {
                "properties": {
                    "Gene_Name": {"type": "string", "description": "Gene symbol"},
                    "Enzyme_Name": {"type": "string", "description": "Enzyme"},
                }
            },
            "RegulationGene": {
                "properties": {
                    "Gene_Name": {"type": "string", "description": "Gene symbol"},
                    "TF_Family": {"type": "string", "description": "TF family"},
                }
            }
        }
    }
}

schema = _load_extract_all_schema(schema_data)

print("Loaded extract_all_genes schema:")
print(f"  Tool name: {schema['function']['name']}")
params = schema['function']['parameters']['properties']
print(f"  Top-level parameters: {list(params.keys())}")
print(f"  Common_Genes fields: {list(params['Common_Genes']['items']['properties'].keys())}")
print(f"  Pathway_Genes fields: {list(params['Pathway_Genes']['items']['properties'].keys())}")
print(f"  Regulation_Genes fields: {list(params['Regulation_Genes']['items']['properties'].keys())}")
print(f"\nFull schema:")
print(json.dumps(schema, indent=2))
