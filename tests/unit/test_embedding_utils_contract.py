from __future__ import annotations

import inspect
from pathlib import Path


def test_embedding_utils_live_in_canonical_retrieval_package():
    import nutrimaster.rag.jina as embedding_utils

    source = inspect.getsource(embedding_utils)

    assert "core.config" not in source
    assert "Settings.from_env" in source
    assert callable(embedding_utils.get_embeddings)
    assert callable(embedding_utils.get_query_embedding)


def test_legacy_embedding_utils_facade_is_removed():
    root = Path(__file__).resolve().parents[2]

    import nutrimaster.rag.jina as canonical

    assert canonical.get_embeddings is not None
    assert canonical.get_query_embedding is not None
    assert not (root / "rag" / "search" / "embedding_utils.py").exists()
