"""
Tests for extract.py schema builder functions.

Run: python -m pytest extractor/tests/test_schema_builders.py -v
"""

from extractor.extract import (
    _schema_props_to_fc,
    _build_extract_all_schema,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  _schema_props_to_fc
# ═══════════════════════════════════════════════════════════════════════════════

class TestSchemaPropsToFc:

    def test_basic(self):
        """Basic: two fields each with description"""
        gene_def = {
            "properties": {
                "Gene_Name": {
                    "title": "Gene_Name",
                    "description": "The name or symbol of the Core Gene, e.g., TaGS5, Pi2, BIK1.",
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "default": "NA",
                },
                "Species": {
                    "title": "Species",
                    "description": "The main species studied (common name).",
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "default": "NA",
                },
            }
        }

        result = _schema_props_to_fc(gene_def)

        assert result == {
            "Gene_Name": {
                "type": "string",
                "description": "The name or symbol of the Core Gene, e.g., TaGS5, Pi2, BIK1.",
            },
            "Species": {
                "type": "string",
                "description": "The main species studied (common name).",
            },
        }

    def test_no_description(self):
        """Missing description defaults to empty string"""
        gene_def = {
            "properties": {
                "Gene_Name": {"title": "Gene_Name"},
            }
        }

        result = _schema_props_to_fc(gene_def)

        assert result == {
            "Gene_Name": {"type": "string", "description": ""},
        }

    def test_empty_properties(self):
        """No properties → empty dict"""
        assert _schema_props_to_fc({}) == {}
        assert _schema_props_to_fc({"properties": {}}) == {}


# ═══════════════════════════════════════════════════════════════════════════════
#  _build_extract_all_schema
# ═══════════════════════════════════════════════════════════════════════════════

class TestBuildExtractAllSchema:

    def test_basic(self):
        """Minimal schema → correct extract_all_genes FC schema"""
        schema_data = {
            "MultipleGeneExtraction": {
                "$defs": {
                    "CommonGene": {
                        "properties": {
                            "Gene_Name": {"description": "Gene name"},
                        }
                    },
                    "PathwayGene": {
                        "properties": {
                            "Gene_Name": {"description": "Gene name"},
                            "Pathway_Name": {"description": "Metabolic pathway"},
                        }
                    },
                    "RegulationGene": {
                        "properties": {
                            "Gene_Name": {"description": "Gene name"},
                            "TF_Family": {"description": "Transcription factor family"},
                        }
                    },
                }
            }
        }

        result = _build_extract_all_schema(schema_data)

        assert result["function"]["name"] == "extract_all_genes"

        params = result["function"]["parameters"]
        assert set(params["required"]) == {
            "Title", "Journal", "DOI",
            "Common_Genes", "Pathway_Genes", "Regulation_Genes",
        }

        common_props = params["properties"]["Common_Genes"]["items"]["properties"]
        assert "Gene_Name" in common_props

        pathway_props = params["properties"]["Pathway_Genes"]["items"]["properties"]
        assert "Pathway_Name" in pathway_props

        regulation_props = params["properties"]["Regulation_Genes"]["items"]["properties"]
        assert "TF_Family" in regulation_props
