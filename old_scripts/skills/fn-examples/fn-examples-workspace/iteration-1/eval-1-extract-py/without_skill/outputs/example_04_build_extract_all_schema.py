"""
example_04_build_extract_all_schema.py

Demonstrates: _build_extract_all_schema(schema_data)

Purpose:
    Builds the "extract_all_genes" function calling schema, which is the
    single-step approach. Instead of classify-then-extract (2 API calls),
    this asks the AI to do everything in one call:
      - Extract Title, Journal, DOI
      - Return three gene arrays: Common_Genes, Pathway_Genes, Regulation_Genes
      - Each array uses its own gene type schema (different fields for each category)

    It reads the "MultipleGeneExtraction" section from the schema file,
    which contains $defs for CommonGene, PathwayGene, and RegulationGene.
"""

import json


def _schema_props_to_fc(gene_def: dict) -> dict:
    fc_props = {}
    for field_name, field_schema in gene_def.get("properties", {}).items():
        desc = field_schema.get("description", "")
        fc_props[field_name] = {"type": "string", "description": desc}
    return fc_props


def _build_extract_all_schema(schema_data: dict) -> dict:
    """Build the extract_all_genes FC schema from MultipleGeneExtraction."""
    multi = schema_data.get("MultipleGeneExtraction", {})
    defs = multi.get("$defs", {})

    common_props = _schema_props_to_fc(defs.get("CommonGene", {}))
    pathway_props = _schema_props_to_fc(defs.get("PathwayGene", {}))
    regulation_props = _schema_props_to_fc(defs.get("RegulationGene", {}))

    return {
        "type": "function",
        "function": {
            "name": "extract_all_genes",
            "description": (
                "Extract paper metadata and ALL core genes at once, classified into "
                "three arrays: Common_Genes, Pathway_Genes, Regulation_Genes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "Title": {"type": "string", "description": "Full paper title."},
                    "Journal": {"type": "string", "description": "Journal name."},
                    "DOI": {"type": "string", "description": "Pure DOI string, no URL prefix."},
                    "Common_Genes": {
                        "type": "array",
                        "description": "Common genes (general function in nutrient metabolism).",
                        "items": {"type": "object", "properties": common_props},
                    },
                    "Pathway_Genes": {
                        "type": "array",
                        "description": "Pathway genes (biosynthetic/metabolic enzyme genes).",
                        "items": {"type": "object", "properties": pathway_props},
                    },
                    "Regulation_Genes": {
                        "type": "array",
                        "description": "Regulation genes (TFs, signaling, regulators).",
                        "items": {"type": "object", "properties": regulation_props},
                    },
                },
                "required": ["Title", "Journal", "DOI", "Common_Genes", "Pathway_Genes", "Regulation_Genes"],
            },
        },
    }


# ── Example: simulate MultipleGeneExtraction schema ──────────────────────

schema_data = {
    "MultipleGeneExtraction": {
        "$defs": {
            "CommonGene": {
                "properties": {
                    "Gene_Name": {"type": "string", "description": "Gene symbol"},
                    "Species": {"type": "string", "description": "Species name"},
                    "Function_Summary": {"type": "string", "description": "Brief function description"}
                }
            },
            "PathwayGene": {
                "properties": {
                    "Gene_Name": {"type": "string", "description": "Gene symbol"},
                    "Enzyme_Name": {"type": "string", "description": "Enzyme name"},
                    "Substrate": {"type": "string", "description": "Enzymatic substrate"},
                    "Product": {"type": "string", "description": "Enzymatic product"}
                }
            },
            "RegulationGene": {
                "properties": {
                    "Gene_Name": {"type": "string", "description": "Gene symbol"},
                    "Regulation_Type": {"type": "string", "description": "Type of regulation (TF, signaling, etc.)"},
                    "Target_Genes": {"type": "string", "description": "Downstream target genes"}
                }
            }
        }
    }
}

result = _build_extract_all_schema(schema_data)
print("extract_all_genes tool schema:")
print(json.dumps(result, indent=2))

# Key difference from _build_extract_schema:
# - This produces THREE gene arrays in a single tool (Common, Pathway, Regulation)
# - Each array has different field definitions matching its gene type
# - The AI fills all three arrays in one API call
