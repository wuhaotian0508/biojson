from __future__ import annotations

import inspect
import json
import pickle
from types import SimpleNamespace
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


def test_legacy_chunk_conversion_preserves_existing_fields():
    from indexing.chunking import GeneChunk
    from indexing.legacy_migration import convert_legacy_chunk

    legacy_chunk = SimpleNamespace(
        gene_name="SIG6",
        paper_title="Greening response",
        journal="American Journal of Botany",
        doi="10.1002/ajb2.1423",
        gene_type="Regulation_Genes",
        content="SIG6 participates in chloroplast development.",
        metadata={"species": "Arabidopsis thaliana"},
        chunk_type="regulation_gene",
        chunker_version="v2.2026-04",
        source_fields=["Gene_Name", "Regulation_Function"],
        relations={"target": "PIF4"},
    )

    converted = convert_legacy_chunk(legacy_chunk)

    assert isinstance(converted, GeneChunk)
    assert converted.__dict__ == legacy_chunk.__dict__


def test_legacy_chunk_conversion_supplies_defaults_for_old_minimal_chunks():
    from indexing.chunking import GeneChunk
    from indexing.legacy_migration import convert_legacy_chunk

    legacy_chunk = SimpleNamespace(
        gene_name="PSY1",
        paper_title="Carotenoid paper",
        journal="Plant Test",
        doi="10.0000/test",
        gene_type="Pathway_Genes",
        content="PSY1 controls carotenoid biosynthesis.",
        metadata={},
    )

    converted = convert_legacy_chunk(legacy_chunk)

    assert isinstance(converted, GeneChunk)
    assert converted.chunk_type == "gene"
    assert converted.source_fields == []
    assert converted.relations == {}


def test_migrate_legacy_index_writes_canonical_chunks_and_reuses_embeddings(tmp_path: Path):
    from indexing.chunking import GeneChunk
    from indexing.legacy_migration import migrate_legacy_index

    source_index = tmp_path / "legacy-index"
    target_index = tmp_path / "new-index"
    source_index.mkdir()
    legacy_chunk = SimpleNamespace(
        gene_name="SIG6",
        paper_title="Greening response",
        journal="American Journal of Botany",
        doi="10.1002/ajb2.1423",
        gene_type="Regulation_Genes",
        content="SIG6 participates in chloroplast development.",
        metadata={},
        chunk_type="regulation_gene",
        chunker_version="v2.2026-04",
        source_fields=["Gene_Name"],
        relations={},
    )
    with (source_index / "chunks.pkl").open("wb") as file:
        pickle.dump([legacy_chunk], file)
    embeddings = np.ones((1, 3), dtype=np.float32)
    np.save(source_index / "embeddings.npy", embeddings)
    (source_index / "manifest.json").write_text('{"files": {}}', encoding="utf-8")

    result = migrate_legacy_index(source_index, target_index)

    with (target_index / "chunks.pkl").open("rb") as file:
        migrated_chunks = pickle.load(file)
    migrated_embeddings = np.load(target_index / "embeddings.npy")

    assert result.chunk_count == 1
    assert migrated_chunks == [
        GeneChunk(
            gene_name="SIG6",
            paper_title="Greening response",
            journal="American Journal of Botany",
            doi="10.1002/ajb2.1423",
            gene_type="Regulation_Genes",
            content="SIG6 participates in chloroplast development.",
            metadata={},
            chunk_type="regulation_gene",
            chunker_version="v2.2026-04",
            source_fields=["Gene_Name"],
            relations={},
        )
    ]
    assert np.array_equal(migrated_embeddings, embeddings)
    assert (target_index / "manifest.json").read_text(encoding="utf-8") == '{"files": {}}'
