from __future__ import annotations

from pathlib import Path

import numpy as np


def test_personal_library_chunks_and_searches_without_legacy_imports(tmp_path: Path):
    import inspect

    from nutrimaster.rag.personal_library import PersonalLibrary
    import nutrimaster.rag.personal_library as personal_module
    from nutrimaster.config.settings import RagSettings

    assert "core.config" not in inspect.getsource(personal_module)
    assert "search.embedding_utils" not in inspect.getsource(personal_module)

    rag_settings = RagSettings.from_env(
        tmp_path,
        {
            "RAG_PERSONAL_LIB_DIR": str(tmp_path / "personal_lib"),
            "CHUNK_SIZE": "10",
            "CHUNK_OVERLAP": "2",
        },
    )
    library = PersonalLibrary(
        "user-1",
        rag_settings=rag_settings,
        embed_texts=lambda texts: np.eye(len(texts), 3, dtype=np.float32),
    )

    chunks = library._chunk_pages("paper.pdf", [(1, "abcdefghij" "klmnop")])
    assert [chunk["metadata"]["page"] for chunk in chunks] == [1, 1]
    assert chunks[0]["content"] == "abcdefghij"

    library.chunks = chunks[:2]
    library.embeddings = np.eye(2, 3, dtype=np.float32)
    results = library.search(np.array([1.0, 0.0, 0.0]), top_k=1)

    assert results[0]["content"] == "abcdefghij"
    assert results[0]["score"] > 0.99


def test_legacy_personal_library_facade_is_removed():
    root = Path(__file__).resolve().parents[2]

    from nutrimaster.rag.personal_library import PersonalLibrary

    assert PersonalLibrary is not None
    assert not (root / "rag" / "search" / "personal_lib.py").exists()
