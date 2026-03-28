"""
_load_extract_schemas — Load all extraction tool schemas from the schema JSON file.

Builds four FC schemas: classify_genes, extract_common_genes, extract_pathway_genes,
and extract_regulation_genes. This is the legacy 2-step approach (classify then extract).

Source: extractor/extract.py:114

Usage:
    python _load_extract_schemas.py
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

# (Inlined from extractor/extract.py:45)

def _build_extract_schema(schema_data: dict, section_key: str, tool_name: str, description: str) -> dict:
    """(Inlined from extractor/extract.py:45)"""
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

# (Inlined from extractor/extract.py:74)

def _build_classify_schema() -> dict:
    """(Inlined from extractor/extract.py:74)"""
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

# --- Target Function ---
# Adapted to accept a schema_path parameter (original reads from SCHEMA_PATH constant).

def _load_extract_schemas(schema_path: str) -> dict:
    """(Adapted from extractor/extract.py:114 — original uses SCHEMA_PATH constant)"""
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_data = json.load(f)

    return {
        "classify_genes": _build_classify_schema(),
        "extract_common_genes": _build_extract_schema(
            schema_data, "CommonGeneExtraction", "extract_common_genes",
            "Extract detailed field information for Common genes.",
        ),
        "extract_pathway_genes": _build_extract_schema(
            schema_data, "PathwayGeneExtraction", "extract_pathway_genes",
            "Extract detailed field information for Pathway genes (biosynthetic/metabolic enzyme genes).",
        ),
        "extract_regulation_genes": _build_extract_schema(
            schema_data, "RegulationGeneExtraction", "extract_regulation_genes",
            "Extract detailed field information for Regulation genes (TFs, signaling, regulators).",
        ),
    }

# --- Sample Input ---
# Create a temporary schema file with a realistic subset of the full schema.
sample_schema = {
    "CommonGeneExtraction": {
        "$defs": {
            "CommonGene": {
                "properties": {
                    "Gene_Name": {"description": "Gene name or symbol."},
                    "Species": {"description": "Main species studied."},
                    "Target_Nutrient": {"description": "Nutrient compound affected."},
                }
            }
        }
    },
    "PathwayGeneExtraction": {
        "$defs": {
            "PathwayGene": {
                "properties": {
                    "Gene_Name": {"description": "Gene name or symbol."},
                    "Enzyme_Activity": {"description": "Enzymatic activity catalyzed."},
                    "Substrate": {"description": "Substrate of the reaction."},
                }
            }
        }
    },
    "RegulationGeneExtraction": {
        "$defs": {
            "RegulationGene": {
                "properties": {
                    "Gene_Name": {"description": "Gene name or symbol."},
                    "TF_Family": {"description": "Transcription factor family."},
                    "Regulatory_Target": {"description": "Direct downstream targets."},
                }
            }
        }
    },
}

# --- Run ---
if __name__ == "__main__":
    # Write schema to a temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(sample_schema, f, indent=2)
        temp_path = f.name

    try:
        schemas = _load_extract_schemas(temp_path)
        print(f"=== Loaded {len(schemas)} tool schemas ===")
        for name, schema in schemas.items():
            func_info = schema["function"]
            param_count = len(func_info["parameters"]["properties"])
            print(f"  {name}: {param_count} top-level parameter(s)")

        print("\n=== Full extract_pathway_genes schema ===")
        print(json.dumps(schemas["extract_pathway_genes"], indent=2, ensure_ascii=False))
    finally:
        os.unlink(temp_path)
