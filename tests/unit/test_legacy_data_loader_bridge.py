from __future__ import annotations

from pathlib import Path


def test_legacy_data_loader_bridge_is_removed():
    root = Path(__file__).resolve().parents[2]

    assert not (root / "rag" / "utils" / "data_loader.py").exists()
