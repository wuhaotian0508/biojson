"""
_load_extract_all_schema — Load the single-step extract_all_genes FC schema
from the schema JSON file.

Reads the schema JSON, then delegates to _build_extract_all_schema to construct
the FC tool definition used in the single-step extraction pipeline.

Source: extractor/extract.py:182

Usage:
    python _load_extract_all_schema.py
"""

import json
import os
import tempfile

# --- Inlined Dependencies ---
# (Inlined from extractor/extract.py:36)

def _schema_props_to_fc(gene_def: dict) -> dict:
    """(Inlined from extractor/extract.py:36)"""
    fc_props = {}
    for field_name, field_schema in gene_def.get("properties", {}).items():
        desc = field_schema.get("description", "")
        fc_props[field_name] = {"type": "string", "description": desc}
    return fc_props

# (Inlined from extractor/extract.py:136)

def _build_extract_all_schema(schema_data: dict) -> dict:
    """(Inlined from extractor/extract.py:136)"""
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

# --- Target Function ---
# Adapted to accept a schema_path parameter (original uses SCHEMA_PATH constant).

def _load_extract_all_schema(schema_path: str) -> dict:
    """(Adapted from extractor/extract.py:182 — original uses SCHEMA_PATH constant)"""
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_data = json.load(f)
    return _build_extract_all_schema(schema_data)

# --- Sample Input ---
# Minimal schema file content representing the MultipleGeneExtraction section.
sample_schema = {
    "MultipleGeneExtraction": {
        "$defs": {
            "CommonGene": {
                "properties": {
                    "Gene_Name": {"description": "Gene name or symbol."},
                    "Species": {"description": "Main species studied."},
                }
            },
            "PathwayGene": {
                "properties": {
                    "Gene_Name": {"description": "Gene name or symbol."},
                    "Enzyme_Activity": {"description": "Enzymatic activity."},
                }
            },
            "RegulationGene": {
                "properties": {
                    "Gene_Name": {"description": "Gene name or symbol."},
                    "TF_Family": {"description": "Transcription factor family."},
                }
            },
        }
    }
}

# --- Run ---
if __name__ == "__main__":
    # Write schema to a temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(sample_schema, f, indent=2)
        temp_path = f.name

    try:
        result = _load_extract_all_schema(temp_path)
        print("=== extract_all_genes FC schema ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    finally:
        os.unlink(temp_path)
