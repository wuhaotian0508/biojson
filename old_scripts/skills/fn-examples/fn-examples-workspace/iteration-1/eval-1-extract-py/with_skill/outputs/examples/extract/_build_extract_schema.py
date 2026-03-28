"""
_build_extract_schema — Build an OpenAI function-calling tool schema from a
schema section (e.g., CommonGeneExtraction, PathwayGeneExtraction).

Reads a section from the full schema JSON, finds the gene type definition in
$defs, and converts its properties to FC format.

Source: extractor/extract.py:45

Usage:
    python _build_extract_schema.py
"""

import json

# --- Inlined Dependencies ---
# (Inlined from extractor/extract.py:36)

def _schema_props_to_fc(gene_def: dict) -> dict:
    """Convert a gene type's properties to FC-compatible format."""
    fc_props = {}
    for field_name, field_schema in gene_def.get("properties", {}).items():
        desc = field_schema.get("description", "")
        fc_props[field_name] = {"type": "string", "description": desc}
    return fc_props

# --- Target Function ---

def _build_extract_schema(schema_data: dict, section_key: str, tool_name: str, description: str) -> dict:
    """Build an OpenAI function calling tool schema from a schema section."""
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
                        "description": f"Detailed information for each gene.",
                        "items": {"type": "object", "properties": gene_props}
                    }
                },
                "required": ["genes"]
            }
        }
    }

# --- Sample Input ---
# A minimal schema_data dict that mimics the structure of nutri_gene_schema_v4.json.
# The "PathwayGeneExtraction" section contains a $defs block with a "PathwayGene"
# type that has properties for enzyme-related gene fields.
schema_data = {
    "PathwayGeneExtraction": {
        "$defs": {
            "PathwayGene": {
                "properties": {
                    "Gene_Name": {
                        "description": "The gene name or symbol, e.g., SlCHI1, OsBCAT2.",
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "default": "NA",
                    },
                    "Species": {
                        "description": "Main species studied (common name).",
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "default": "NA",
                    },
                    "Enzyme_Activity": {
                        "description": "Specific enzymatic activity catalyzed by this gene product.",
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "default": "NA",
                    },
                    "Substrate": {
                        "description": "The substrate of the enzymatic reaction.",
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "default": "NA",
                    },
                    "Product": {
                        "description": "The product of the enzymatic reaction.",
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "default": "NA",
                    },
                }
            }
        }
    }
}

# --- Run ---
if __name__ == "__main__":
    result = _build_extract_schema(
        schema_data,
        section_key="PathwayGeneExtraction",
        tool_name="extract_pathway_genes",
        description="Extract detailed field information for Pathway genes (biosynthetic/metabolic enzyme genes).",
    )
    print("=== extract_pathway_genes FC schema ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
