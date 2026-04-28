from __future__ import annotations

import inspect
from pathlib import Path


def test_crispr_tool_loads_canonical_pipeline_namespace():
    import nutrimaster.agent.tools.crispr as crispr_tool_module

    source = inspect.getsource(crispr_tool_module)

    assert "rag.skills.crispr_experiment" not in source
    assert "crispr.pipeline" in source


def test_legacy_crispr_skill_directory_is_removed_after_cutover():
    root = Path(__file__).resolve().parents[2]
    legacy_dir = root / "rag" / "skills"

    assert not legacy_dir.exists()
