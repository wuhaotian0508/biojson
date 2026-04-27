from __future__ import annotations

from pathlib import Path


def test_admin_uses_canonical_retriever_without_sys_path_hack():
    root = Path(__file__).resolve().parents[2]
    source = (root / "src" / "admin" / "app.py").read_text(encoding="utf-8")

    assert not (root / "admin").exists()
    assert "_sys.path.insert" not in source
    assert "from retriever import JinaRetriever" not in source
    assert "from retrieval.jina_retriever import JinaRetriever" in source
