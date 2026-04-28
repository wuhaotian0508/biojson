from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]

from nutrimaster.rag.chunking import CHUNKER_VERSION, GeneChunk
from nutrimaster.rag.incremental_indexer import IncrementalIndexer, sha256_of


def _write_manifest(index_dir: Path, filename: str, sha: str, n_chunks: int) -> None:
    (index_dir / "manifest.json").write_text(
        json.dumps(
            {
                "chunker_version": CHUNKER_VERSION,
                "files": {
                    filename: {
                        "sha": sha,
                        "chunker_version": CHUNKER_VERSION,
                        "n_chunks": n_chunks,
                        "start": 0,
                        "end": n_chunks,
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _sample_chunk() -> GeneChunk:
    return GeneChunk(
        gene_name="PSY1",
        paper_title="Pilot carotenoid paper",
        journal="Plant Test",
        doi="10.0000/test",
        gene_type="Pathway_Genes",
        content="PSY1 controls carotenoid biosynthesis in tomato fruit.",
        metadata={"species": "Solanum lycopersicum"},
        chunk_type="pathway_gene",
        chunker_version=CHUNKER_VERSION,
        source_fields=["Gene"],
        relations={},
    )


def test_rebuilds_when_manifest_matches_but_index_artifacts_are_missing(tmp_path: Path):
    data_dir = tmp_path / "data"
    index_dir = tmp_path / "index"
    data_dir.mkdir()
    index_dir.mkdir()
    json_file = data_dir / "paper_nutri_plant_verified.json"
    json_file.write_text("{}", encoding="utf-8")
    _write_manifest(index_dir, json_file.name, sha256_of(json_file), n_chunks=1)

    load_calls = []

    def load_paper(path: Path) -> list[GeneChunk]:
        load_calls.append(path.name)
        return [_sample_chunk()]

    def embed(texts: list[str]) -> np.ndarray:
        return np.ones((len(texts), 3), dtype=np.float32)

    chunks, embeddings = IncrementalIndexer(index_dir, data_dir, embed).build_incremental(
        load_paper_fn=load_paper,
    )

    assert load_calls == [json_file.name]
    assert len(chunks) == 1
    assert embeddings is not None
    assert embeddings.shape == (1, 3)


def test_rebuilds_when_manifest_ranges_cannot_be_satisfied_by_old_index(tmp_path: Path):
    data_dir = tmp_path / "data"
    index_dir = tmp_path / "index"
    data_dir.mkdir()
    index_dir.mkdir()
    json_file = data_dir / "paper_nutri_plant_verified.json"
    json_file.write_text("{}", encoding="utf-8")
    _write_manifest(index_dir, json_file.name, sha256_of(json_file), n_chunks=1)

    with (index_dir / "chunks.pkl").open("wb") as f:
        pickle.dump([], f)
    np.save(index_dir / "embeddings.npy", np.zeros((0, 3), dtype=np.float32))

    def load_paper(path: Path) -> list[GeneChunk]:
        return [_sample_chunk()]

    def embed(texts: list[str]) -> np.ndarray:
        return np.ones((len(texts), 3), dtype=np.float32)

    chunks, embeddings = IncrementalIndexer(index_dir, data_dir, embed).build_incremental(
        load_paper_fn=load_paper,
    )

    assert len(chunks) == 1
    assert embeddings is not None
    assert embeddings.shape == (1, 3)
