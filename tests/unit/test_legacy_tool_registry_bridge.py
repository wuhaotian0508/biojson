from __future__ import annotations

from pathlib import Path


def test_legacy_tool_registry_facade_is_removed():
    root = Path(__file__).resolve().parents[2]

    from agent.tools import ToolRegistry

    assert ToolRegistry is not None
    assert not (root / "rag" / "tools" / "registry.py").exists()
