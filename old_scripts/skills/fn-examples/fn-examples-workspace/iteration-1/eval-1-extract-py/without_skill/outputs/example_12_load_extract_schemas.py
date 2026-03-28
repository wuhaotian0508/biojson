"""
example_12_load_extract_schemas.py

Demonstrates: _load_extract_schemas()

Purpose:
    Loads ALL four extraction tool schemas from the schema JSON file.
    This is used in the legacy 2-step extraction approach.

    It returns a dict with four keys:
      - "classify_genes"          -> schema for step 1 (classification)
      - "extract_common_genes"    -> schema for Common gene details
      - "extract_pathway_genes"   -> schema for Pathway gene details
      - "extract_regulation_genes"-> schema for Regulation gene details

    Each value is a complete OpenAI function calling tool definition.

    This example simulates the function using an in-memory schema dict
    instead of reading from disk.
"""

import json


def _schema_props_to_fc(gene_def: dict) -> dict:
    fc_props = {}
    for field_name, field_schema in gene_def.get("properties", {}).items():
        desc = field_schema.get("description", "")
        fc_props[field_name] = {"type": "string", "description": desc}
    return fc_props


def _build_classify_schema() -> dict:
    return {
        "type": "function",
        "function": {
            "name": "classify_genes",
            "description": "Identify ALL core genes and classify each into Common / Pathway / Regulation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "Title": {"type": "string", "description": "Full paper title."},
                    "Journal": {"type": "string", "description": "Journal name."},
                    "DOI": {"type": "string", "description": "DOI string."},
                    "genes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "Gene_Name": {"type": "string"},
                                "category": {"type": "string", "enum": ["Common", "Pathway", "Regulation"]},
                            },
                            "required": ["Gene_Name", "category"],
                        },
                    },
                },
                "required": ["Title", "Journal", "DOI", "genes"],
            },
        },
    }


def _build_extract_schema(schema_data, section_key, tool_name, description):
    section = schema_data.get(section_key, {})
    defs = section.get("$defs", {})
    gene_type_name = list(defs.keys())[0] if defs else None
    gene_props = {}
    if gene_type_name:
        gene_props = _schema_props_to_fc(defs[gene_type_name])
    return {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    "genes": {
                        "type": "array",
                        "items": {"type": "object", "properties": gene_props}
                    }
                },
                "required": ["genes"]
            }
        }
    }


def _load_extract_schemas(schema_data):
    """Load all extraction tool schemas (simulated without file I/O)."""
    return {
        "classify_genes": _build_classify_schema(),
        "extract_common_genes": _build_extract_schema(
            schema_data, "CommonGeneExtraction", "extract_common_genes",
            "Extract detailed field information for Common genes.",
        ),
        "extract_pathway_genes": _build_extract_schema(
            schema_data, "PathwayGeneExtraction", "extract_pathway_genes",
            "Extract detailed field information for Pathway genes.",
        ),
        "extract_regulation_genes": _build_extract_schema(
            schema_data, "RegulationGeneExtraction", "extract_regulation_genes",
            "Extract detailed field information for Regulation genes.",
        ),
    }


# ── Example: Build all schemas from a simulated schema file ──────────────

schema_data = {
    "CommonGeneExtraction": {
        "$defs": {
            "CommonGene": {
                "properties": {
                    "Gene_Name": {"type": "string", "description": "Gene symbol"},
                    "Species": {"type": "string", "description": "Species name"},
                }
            }
        }
    },
    "PathwayGeneExtraction": {
        "$defs": {
            "PathwayGene": {
                "properties": {
                    "Gene_Name": {"type": "string", "description": "Gene symbol"},
                    "Enzyme_Name": {"type": "string", "description": "Enzyme name"},
                    "Substrate": {"type": "string", "description": "Substrate"},
                }
            }
        }
    },
    "RegulationGeneExtraction": {
        "$defs": {
            "RegulationGene": {
                "properties": {
                    "Gene_Name": {"type": "string", "description": "Gene symbol"},
                    "Regulation_Type": {"type": "string", "description": "TF, signaling, etc."},
                    "Target_Genes": {"type": "string", "description": "Downstream targets"},
                }
            }
        }
    }
}

schemas = _load_extract_schemas(schema_data)

print(f"Loaded {len(schemas)} tool schemas:")
for name, schema in schemas.items():
    func = schema["function"]
    param_count = len(func["parameters"]["properties"])
    print(f"  - {name}: {param_count} top-level parameters")

print(f"\nFull 'extract_pathway_genes' schema:")
print(json.dumps(schemas["extract_pathway_genes"], indent=2))
