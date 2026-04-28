from __future__ import annotations


def test_skill_loader_parses_shared_and_user_skills(tmp_path):
    from nutrimaster.agent.skills import SkillLoader

    skills_dir = tmp_path / "skills"
    user_skills_dir = tmp_path / "user_skills"
    (skills_dir / "rag_answer").mkdir(parents=True)
    (skills_dir / "rag_answer" / "skill.md").write_text(
        """---
name: rag-answer
description: >
  Answer questions with RAG.
tools: [rag_search, read_tool]
---
Use RAG.
""",
        encoding="utf-8",
    )
    (user_skills_dir / "user-1" / "custom").mkdir(parents=True)
    (user_skills_dir / "user-1" / "custom" / "skill.md").write_text(
        """---
name: custom
description: User custom skill.
tools: all
---
Custom content.
""",
        encoding="utf-8",
    )

    loader = SkillLoader(skills_dir=skills_dir, user_skills_dir=user_skills_dir)

    skills = {skill.name: skill for skill in loader.list_dir("user-1")}
    assert skills["rag-answer"].tools == ["rag_search", "read_tool"]
    assert skills["custom"].tools is None
    assert skills["custom"].content == "Custom content."
    assert skills["custom"].is_shared is False


def test_skill_loader_builds_crispr_sop_tool_call():
    from nutrimaster.agent.skills import SkillLoader

    loader = SkillLoader(skills_dir=None, user_skills_dir=None)

    assert loader.build_tool_call("请给我 GmFAD2 的 CRISPR SOP") == {
        "type": "tool_call",
        "tool": "run_crispr_pipeline",
        "skill": "crispr-experiment",
        "args": {"query": "请给我 GmFAD2 的 CRISPR SOP"},
    }
    assert loader.build_tool_call("请给我 GmFAD2 的 CRISPR 实验方案") is None


def test_gene_name_detection_is_local_to_nutrimaster():
    from nutrimaster.agent.skills import extract_gene_names

    assert extract_gene_names("编辑 GmFAD2 和 AtMYB4，GmFAD2 是靶点") == [
        "GmFAD2",
        "AtMYB4",
    ]
    assert "SpCas9" not in extract_gene_names("使用 SpCas9 对 OsNAS2 进行编辑")
    assert extract_gene_names("GmFAD2之类的基因") == []
