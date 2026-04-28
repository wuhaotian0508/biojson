from __future__ import annotations

from pathlib import Path


def test_admin_uses_canonical_retriever_without_sys_path_hack():
    root = Path(__file__).resolve().parents[2]
    source = (root / "src" / "nutrimaster" / "web" / "admin" / "app.py").read_text(encoding="utf-8")

    assert not (root / "admin").exists()
    assert "_sys.path.insert" not in source
    assert "from retriever import JinaRetriever" not in source
    assert "from nutrimaster.rag.jina_retriever import JinaRetriever" in source


def test_admin_pipeline_uses_incremental_index_refresh_hook():
    root = Path(__file__).resolve().parents[2]
    source = (root / "src" / "nutrimaster" / "web" / "admin" / "app.py").read_text(encoding="utf-8")

    assert "def configure_index_refresh(" in source
    assert "_refresh_index(DATA_DIR, force=False)" in source
    assert "retriever.build_index(data_dir=DATA_DIR, force=True)" not in source
