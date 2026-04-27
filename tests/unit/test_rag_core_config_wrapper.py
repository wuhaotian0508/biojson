from __future__ import annotations


def test_rag_core_config_exports_canonical_settings():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]

    assert not (root / "rag" / "config.py").exists()
    assert not (root / "rag" / "core" / "config.py").exists()
