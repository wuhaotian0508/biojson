"""
_build_extract_all_schema — Build the single-step extract_all_genes FC schema
from the MultipleGeneExtraction section of the schema JSON.

Produces one function-calling tool that extracts Title, Journal, DOI, plus three
gene arrays (Common_Genes, Pathway_Genes, Regulation_Genes) in a single API call.

Source: extractor/extract.py:136

Usage:
    python _build_extract_all_schema.py
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

def _build_extract_all_schema(schema_data: dict) -> dict:
    """Build the extract_all_genes FC schema from MultipleGeneExtraction."""
    multi = schema_data.get("MultipleGeneExtraction", {})
    defs = multi.get("$defs", {})

    # Build FC properties for each gene type
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

# --- Sample Input ---
# Mimics the MultipleGeneExtraction section of nutri_gene_schema_v4.json.
# Each gene type (Common, Pathway, Regulation) has a different set of fields.
schema_data = {
    "MultipleGeneExtraction": {
        "$defs": {
            "CommonGene": {
                "properties": {
                    "Gene_Name": {
                        "description": "The gene name or symbol.",
                    },
                    "Species": {
                        "description": "Main species studied (common name).",
                    },
                    "Target_Nutrient": {
                        "description": "The nutrient compound affected.",
                    },
                }
            },
            "PathwayGene": {
                "properties": {
                    "Gene_Name": {
                        "description": "The gene name or symbol.",
                    },
                    "Enzyme_Activity": {
                        "description": "Specific enzymatic activity.",
                    },
                    "Substrate": {
                        "description": "Substrate of the enzymatic reaction.",
                    },
                    "Product": {
                        "description": "Product of the enzymatic reaction.",
                    },
                }
            },
            "RegulationGene": {
                "properties": {
                    "Gene_Name": {
                        "description": "The gene name or symbol.",
                    },
                    "TF_Family": {
                        "description": "Transcription factor family.",
                    },
                    "Regulatory_Target": {
                        "description": "Direct downstream target genes.",
                    },
                }
            },
        }
    }
}

# --- Run ---
if __name__ == "__main__":
    result = _build_extract_all_schema(schema_data)
    print("=== extract_all_genes FC schema ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
