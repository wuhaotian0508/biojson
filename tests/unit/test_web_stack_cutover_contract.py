from __future__ import annotations

from pathlib import Path


def test_web_app_uses_canonical_stack_instead_of_manual_legacy_tool_wiring():
    root = Path(__file__).resolve().parents[2]
    source = (root / "src" / "server" / "web.py").read_text(encoding="utf-8")

    assert not (root / "rag" / "web").exists()
    assert "build_legacy_agent_stack" in source
    assert "sys.path.insert" not in source
    assert "import core.config" not in source
    assert "from search." not in source
    assert "from web.auth" not in source
    assert "from skills." not in source
    assert "Settings.from_env" in source
    assert "from core.agent import Agent" not in source
    assert "from skills.skill_loader" not in source
    assert "from search.reranker" not in source


def test_web_app_injects_global_retriever_into_admin_index_refresh():
    root = Path(__file__).resolve().parents[2]
    source = (root / "src" / "server" / "web.py").read_text(encoding="utf-8")

    assert "configure_index_refresh(_refresh_admin_index)" in source
    assert "retriever.build_index(data_dir=data_dir, incremental=True, force=force)" in source
