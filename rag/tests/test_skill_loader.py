"""
skill_loader 单元测试

测试内容：
1. 技能注册：扫描 skills/ 目录并正确加载 SKILL.md
2. 触发条件：query 触发需要 sop + 基因编辑操作 + 具体基因名
3. 基因名提取：extract_gene_names() 的去重、排除逻辑
"""
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAG_DIR = ROOT / "rag"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(RAG_DIR))


def test_skill_loader_registers_crispr_skill():
    """测试 SkillLoader 能正确扫描并注册 crispr-experiment 技能"""
    loader_module = importlib.import_module("rag.skills.skill_loader")
    loader = loader_module.SkillLoader(RAG_DIR / "skills")

    skill = loader.get_skill("crispr-experiment")

    assert skill.name == "crispr-experiment"
    assert "crispr" in skill.tags
    assert skill.path.name == "SKILL.md"


def test_skill_loader_builds_tool_call_for_direct_query():
    """
    测试 query 触发 SOP：必须同时包含 sop + 基因编辑操作 + 具体基因名
    示例输入："请直接给我 GmMYB4 CRISPR 实验方案 SOP"
    """
    loader_module = importlib.import_module("rag.skills.skill_loader")
    loader = loader_module.SkillLoader(RAG_DIR / "skills")

    # ---- 包含 "SOP" + CRISPR + 具体基因名 → 应触发 ----
    tool_call = loader.build_tool_call(
        query="请直接给我 Glycine max 的 GmMYB4 CRISPR 实验方案 SOP",
        trigger_source="query",
    )
    assert tool_call is not None
    assert tool_call["type"] == "tool_call"
    assert tool_call["tool"] == "run_crispr_pipeline"
    assert tool_call["skill"] == "crispr-experiment"
    assert tool_call["args"]["query"].startswith("请直接给我")


def test_query_trigger_requires_sop_keyword():
    """
    测试 query 触发只需包含 "sop"（不区分大小写）
    没有 sop 关键词时不应触发
    """
    loader_module = importlib.import_module("rag.skills.skill_loader")
    loader = loader_module.SkillLoader(RAG_DIR / "skills")

    # ---- 没有 "sop" → 不应触发 ----
    tool_call = loader.build_tool_call(
        query="请帮我设计 GmFAD2 的 CRISPR 敲除实验方案",
        trigger_source="query",
    )
    assert tool_call is None

    # ---- 加上 "SOP" 后应触发 ----
    tool_call = loader.build_tool_call(
        query="请帮我设计 GmFAD2 的 CRISPR 敲除 SOP",
        trigger_source="query",
    )
    assert tool_call is not None

    # ---- 小写 "sop" 也应触发 ----
    tool_call = loader.build_tool_call(
        query="请帮我设计 GmFAD2 的 CRISPR 敲除 sop",
        trigger_source="query",
    )
    assert tool_call is not None

    # ---- 混合大小写 "Sop" 也应触发 ----
    tool_call = loader.build_tool_call(
        query="请帮我设计 GmFAD2 的 CRISPR 敲除 Sop",
        trigger_source="query",
    )
    assert tool_call is not None

    # ---- 中文紧邻 sop（如"的sop"）也应触发 ----
    tool_call = loader.build_tool_call(
        query="给我玉米Shrunken-2和Opaque-2的sop",
        trigger_source="query",
    )
    assert tool_call is not None


def test_extract_gene_names():
    """
    测试基因名提取：去重、排除 CRISPR 工具名、排除泛指表述
    """
    loader_module = importlib.import_module("rag.skills.skill_loader")

    # ---- 正常提取 ----
    text = "建议对 GmFAD2 和 AtMYB4 进行 CRISPR 编辑，GmFAD2 是关键靶点"
    names = loader_module.SkillLoader.extract_gene_names(text)
    assert names == ["GmFAD2", "AtMYB4"]  # 去重，保持顺序

    # ---- 排除 CRISPR 工具名 ----
    text = "使用 SpCas9 对 OsNAS2 进行编辑"
    names = loader_module.SkillLoader.extract_gene_names(text)
    assert "SpCas9" not in names
    assert "OsNAS2" in names

    # ---- 排除泛指表述 ----
    text = "GmFAD2之类的基因都可以考虑"
    names = loader_module.SkillLoader.extract_gene_names(text)
    assert names == []  # "之类" 后缀应排除
