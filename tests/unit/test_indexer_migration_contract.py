from __future__ import annotations

import inspect
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]


def test_index_service_uses_canonical_incremental_indexer():
    import indexing.index_service as index_service_module

    source = inspect.getsource(index_service_module)

    assert "utils.indexer" not in source
    assert "indexing.incremental_indexer" in source


def test_legacy_indexer_facade_is_removed():
    from indexing.incremental_indexer import IncrementalIndexer, sha256_of

    assert IncrementalIndexer is not None
    assert sha256_of is not None
    assert not (ROOT / "rag" / "utils" / "indexer.py").exists()


def test_canonical_incremental_indexer_builds_with_nutrimaster_chunks(tmp_path: Path):
    from indexing.chunking import CHUNKER_VERSION, GeneChunk
    from indexing.incremental_indexer import IncrementalIndexer, sha256_of

    data_dir = tmp_path / "data"
    index_dir = tmp_path / "index"
    data_dir.mkdir()
    index_dir.mkdir()
    json_file = data_dir / "paper_nutri_plant_verified.json"
    json_file.write_text("{}", encoding="utf-8")

    def load_paper(path: Path) -> list[GeneChunk]:
        assert path == json_file
        return [
            GeneChunk(
                gene_name="PSY1",
                paper_title="Pilot carotenoid paper",
                journal="Plant Test",
                doi="10.0000/test",
                gene_type="Pathway_Genes",
                content="PSY1 controls carotenoid biosynthesis in tomato fruit.",
                metadata={},
            )
        ]

    def embed(texts: list[str]) -> np.ndarray:
        assert texts == ["PSY1 controls carotenoid biosynthesis in tomato fruit."]
        return np.ones((len(texts), 3), dtype=np.float32)

    chunks, embeddings = IncrementalIndexer(
        index_dir=index_dir,
        data_dir=data_dir,
        embed_fn=embed,
    ).build_incremental(load_paper_fn=load_paper)

    manifest = json.loads((index_dir / "manifest.json").read_text(encoding="utf-8"))
    assert chunks[0].gene_name == "PSY1"
    assert embeddings is not None
    assert embeddings.shape == (1, 3)
    assert manifest["chunker_version"] == CHUNKER_VERSION
    assert manifest["files"][json_file.name]["sha"] == sha256_of(json_file)
