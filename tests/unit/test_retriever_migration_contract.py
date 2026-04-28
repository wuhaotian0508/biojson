from __future__ import annotations

import importlib
import pickle
from pathlib import Path
from unittest.mock import patch

import numpy as np


ROOT = Path(__file__).resolve().parents[2]


def test_web_services_use_canonical_jina_retriever():
    import nutrimaster.web.deps as deps_module

    source = Path(deps_module.__file__).read_text(encoding="utf-8")

    assert "search.retriever" not in source
    assert "nutrimaster.rag.jina" in source


def test_legacy_search_retriever_facade_is_removed():
    canonical_retriever = importlib.import_module("nutrimaster.rag.jina")

    assert hasattr(canonical_retriever, "JinaRetriever")
    assert not (ROOT / "rag" / "search" / "retriever.py").exists()


def test_jina_retriever_loads_existing_index_on_initialization(tmp_path: Path):
    from nutrimaster.config.settings import RagSettings, Settings
    from nutrimaster.rag.gene_index import GeneChunk
    from nutrimaster.rag.jina import JinaRetriever

    data_dir = tmp_path / "data"
    index_dir = tmp_path / "index"
    data_dir.mkdir()
    index_dir.mkdir()
    chunk = GeneChunk(
        gene_name="GAME8",
        paper_title="Stereo-divergent alkaloids",
        journal="Nature Communications",
        doi="10.example/game8",
        gene_type="Pathway_Genes",
        content="GAME8 determines C25 stereochemistry in Solanaceae alkaloids.",
        metadata={},
    )
    with (index_dir / "chunks.pkl").open("wb") as file:
        pickle.dump([chunk], file)
    np.save(index_dir / "embeddings.npy", np.ones((1, 3), dtype=np.float32))

    settings = Settings(
        project_root=tmp_path,
        jina_api_key="test-key",
        rag=RagSettings(
            data_dir=data_dir,
            index_dir=index_dir,
            personal_lib_dir=tmp_path / "personal",
        ),
    )

    retriever = JinaRetriever(settings=settings)

    assert len(retriever.chunks) == 1
    assert retriever.chunks[0].gene_name == "GAME8"
    assert retriever.embeddings is not None
    assert retriever.embeddings.shape == (1, 3)


def test_jina_retriever_reports_unreadable_index_without_crashing(tmp_path: Path):
    from nutrimaster.config.settings import RagSettings, Settings
    from nutrimaster.rag.jina import JinaRetriever

    data_dir = tmp_path / "data"
    index_dir = tmp_path / "index"
    data_dir.mkdir()
    index_dir.mkdir()
    (index_dir / "chunks.pkl").write_bytes(b"legacy pickle")
    np.save(index_dir / "embeddings.npy", np.ones((1, 3), dtype=np.float32))

    settings = Settings(
        project_root=tmp_path,
        jina_api_key="test-key",
        rag=RagSettings(
            data_dir=data_dir,
            index_dir=index_dir,
            personal_lib_dir=tmp_path / "personal",
        ),
    )

    with patch("nutrimaster.rag.jina.pickle.load") as load:
        load.side_effect = ModuleNotFoundError("No module named 'indexing.chunking'")
        retriever = JinaRetriever(settings=settings)

    status = retriever.index_status()
    assert retriever.chunks == []
    assert retriever.embeddings is None
    assert status["load_error"] == "ModuleNotFoundError: No module named 'indexing.chunking'"
