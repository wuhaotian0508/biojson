"""
example_02_build_extract_schema.py

Demonstrates: _build_extract_schema(schema_data, section_key, tool_name, description)

Purpose:
    Builds an OpenAI function calling tool definition from a section of the
    schema JSON file. It extracts the gene type definition from "$defs",
    converts its properties to FC format, and wraps everything in the
    standard OpenAI tools structure: {type: "function", function: {name, description, parameters}}.

    The resulting schema tells the API "call this function with a 'genes' array
    where each gene has these string fields."
"""

import json


def _schema_props_to_fc(gene_def: dict) -> dict:
    fc_props = {}
    for field_name, field_schema in gene_def.get("properties", {}).items():
        desc = field_schema.get("description", "")
        fc_props[field_name] = {"type": "string", "description": desc}
    return fc_props


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
                        "description": "Detailed information for each gene.",
                        "items": {"type": "object", "properties": gene_props}
                    }
                },
                "required": ["genes"]
            }
        }
    }


# ── Example: simulate a schema file with a PathwayGeneExtraction section ──

schema_data = {
    "PathwayGeneExtraction": {
        "$defs": {
            "PathwayGene": {
                "properties": {
                    "Gene_Name": {
                        "type": "string",
                        "description": "Gene symbol, e.g. CHS, CHI, F3H"
                    },
                    "Enzyme_Name": {
                        "type": "string",
                        "description": "Name of the enzyme encoded by this gene"
                    },
                    "Substrate": {
                        "type": "string",
                        "description": "Substrate of the enzymatic reaction"
                    },
                    "Product": {
                        "type": "string",
                        "description": "Product of the enzymatic reaction"
                    }
                }
            }
        }
    }
}

result = _build_extract_schema(
    schema_data,
    section_key="PathwayGeneExtraction",
    tool_name="extract_pathway_genes",
    description="Extract detailed field information for Pathway genes."
)

print("Generated OpenAI function calling tool schema:")
print(json.dumps(result, indent=2))

# The output is ready to be passed directly to the OpenAI API as:
#   response = client.chat.completions.create(
#       ...,
#       tools=[result],
#       tool_choice={"type": "function", "function": {"name": "extract_pathway_genes"}}
#   )
