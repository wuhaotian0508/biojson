"""
测试 extract.py 中所有 schema 构建相关函数。
每个函数都有输入样例和预期输出，帮助快速理解函数作用。

运行方式：
    cd /data/haotianwu/biojson
    python -m pytest extractor/tests/test_schema_builders.py -v
"""

import json
import sys
from pathlib import Path

# 让 import 能正确找到 extractor 包
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from extractor.extract import (
    _schema_props_to_fc,
    _build_extract_schema,
    _build_classify_schema,
    _build_extract_all_schema,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  _schema_props_to_fc
#  作用：把 schema JSON 里某个 gene 类型的 properties 转成 OpenAI function calling 格式。
#        原始 schema 的字段可能有 anyOf、default 等复杂结构，
#        这个函数统一简化为 {"type": "string", "description": "..."} 格式。
# ═══════════════════════════════════════════════════════════════════════════════

class TestSchemaPropsToFc:

    def test_basic(self):
        """最基础的场景：两个字段各有 description"""
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

        # 输出被简化为统一的 {type: string, description: ...} 格式
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
        """如果原始 schema 中字段没有 description，返回空字符串"""
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
        """没有 properties 时返回空 dict"""
        assert _schema_props_to_fc({}) == {}
        assert _schema_props_to_fc({"properties": {}}) == {}


# ═══════════════════════════════════════════════════════════════════════════════
#  _build_extract_schema
#  作用：从完整的 schema JSON 中，针对某个 section（如 CommonGeneExtraction）
#        构建一个 OpenAI function calling tool 的完整定义。
#
#  输入：schema_data（完整 JSON）, section_key, tool_name, description
#  输出：一个符合 OpenAI tools 格式的 dict，包含 function.name, function.parameters 等
# ═══════════════════════════════════════════════════════════════════════════════

class TestBuildExtractSchema:

    def test_basic(self):
        """用一个最小的 schema 结构来演示"""
        schema_data = {
            "CommonGeneExtraction": {
                "$defs": {
                    "CommonGene": {
                        "description": "Common gene",
                        "properties": {
                            "Gene_Name": {
                                "description": "Gene name or symbol.",
                            },
                            "Species": {
                                "description": "Species name.",
                            },
                        },
                    }
                }
            }
        }

        result = _build_extract_schema(
            schema_data,
            section_key="CommonGeneExtraction",
            tool_name="extract_common_genes",
            description="Extract detailed field information for Common genes.",
        )

        # 验证外层结构
        assert result["type"] == "function"
        assert result["function"]["name"] == "extract_common_genes"
        assert result["function"]["description"] == "Extract detailed field information for Common genes."

        # 验证 parameters 结构
        params = result["function"]["parameters"]
        assert params["type"] == "object"
        assert "genes" in params["properties"]
        assert params["required"] == ["genes"]

        # 验证 genes 数组里每个 item 的 properties
        gene_item_props = params["properties"]["genes"]["items"]["properties"]
        assert "Gene_Name" in gene_item_props
        assert "Species" in gene_item_props
        assert gene_item_props["Gene_Name"]["type"] == "string"

    def test_missing_section(self):
        """如果 section_key 不存在，仍然返回有效结构（空 gene_props）"""
        result = _build_extract_schema({}, "NonExistent", "test_tool", "desc")
        gene_items = result["function"]["parameters"]["properties"]["genes"]["items"]
        assert gene_items["properties"] == {}


# ═══════════════════════════════════════════════════════════════════════════════
#  _build_classify_schema
#  作用：构建 classify_genes 的 function calling schema（硬编码，不依赖文件）。
#        这个 tool 用于第一步分类：识别论文中所有基因并归类为 Common/Pathway/Regulation。
# ═══════════════════════════════════════════════════════════════════════════════

class TestBuildClassifySchema:

    def test_structure(self):
        result = _build_classify_schema()

        assert result["type"] == "function"
        assert result["function"]["name"] == "classify_genes"

        params = result["function"]["parameters"]
        assert "Title" in params["properties"]
        assert "Journal" in params["properties"]
        assert "DOI" in params["properties"]
        assert "genes" in params["properties"]

        # genes 里面每个 item 有 Gene_Name, category, reason
        gene_item = params["properties"]["genes"]["items"]
        assert "Gene_Name" in gene_item["properties"]
        assert "category" in gene_item["properties"]
        assert gene_item["properties"]["category"]["enum"] == ["Common", "Pathway", "Regulation"]

        # required 字段
        assert set(params["required"]) == {"Title", "Journal", "DOI", "genes"}


# ═══════════════════════════════════════════════════════════════════════════════
#  _build_extract_all_schema
#  作用：构建 extract_all_genes 的 FC schema，用于单步提取。
#        从 schema JSON 的 MultipleGeneExtraction 里读取三种基因类型的字段定义，
#        合并成一个包含 Title/Journal/DOI + 三个基因数组的大 schema。
# ═══════════════════════════════════════════════════════════════════════════════

class TestBuildExtractAllSchema:

    def test_basic(self):
        """用最小 schema 演示 extract_all_genes 的 schema 构建"""
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

        # Common_Genes 只有 Gene_Name
        common_props = params["properties"]["Common_Genes"]["items"]["properties"]
        assert "Gene_Name" in common_props

        # Pathway_Genes 有 Gene_Name + Pathway_Name
        pathway_props = params["properties"]["Pathway_Genes"]["items"]["properties"]
        assert "Pathway_Name" in pathway_props

        # Regulation_Genes 有 Gene_Name + TF_Family
        regulation_props = params["properties"]["Regulation_Genes"]["items"]["properties"]
        assert "TF_Family" in regulation_props
