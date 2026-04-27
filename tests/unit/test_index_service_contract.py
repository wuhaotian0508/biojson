from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np


def test_index_service_builds_with_injected_legacy_dependencies(tmp_path: Path):
    from indexing.index_service import IndexBuildResult, IndexService

    calls = []

    class FakeIndexer:
        def __init__(self, index_dir, data_dir, embed_fn):
            self.index_dir = index_dir
            self.data_dir = data_dir
            self.embed_fn = embed_fn

        def build_incremental(self, *, force, load_paper_fn):
            calls.append((self.index_dir, self.data_dir, force, load_paper_fn("paper.json")))
            return ["chunk-a", "chunk-b"], np.zeros((2, 4), dtype=np.float32)

    service = IndexService(
        data_dir=tmp_path / "data",
        index_dir=tmp_path / "index",
        embed_texts=lambda texts: np.zeros((len(texts), 4), dtype=np.float32),
        load_paper=lambda path: [f"loaded:{path}"],
        indexer_cls=FakeIndexer,
    )

    result = service.build(force=True)

    assert isinstance(result, IndexBuildResult)
    assert result.chunk_count == 2
    assert result.embedding_shape == (2, 4)
    assert result.index_dir == tmp_path / "index"
    assert calls == [
        (tmp_path / "index", tmp_path / "data", True, ["loaded:paper.json"])
    ]


def test_index_service_can_use_real_legacy_indexer_with_fake_embedding(tmp_path: Path):
    from indexing.index_service import IndexService

    data_dir = tmp_path / "data"
    index_dir = tmp_path / "index"
    data_dir.mkdir()
    index_dir.mkdir()
    json_file = data_dir / "paper_nutri_plant_verified.json"
    json_file.write_text("{}", encoding="utf-8")

    def load_paper(path: Path) -> list[SimpleNamespace]:
        return [
            SimpleNamespace(
                gene_name="PSY1",
                paper_title="Pilot carotenoid paper",
                journal="Plant Test",
                doi="10.0000/test",
                gene_type="Pathway_Genes",
                content="PSY1 controls carotenoid biosynthesis in tomato fruit.",
                metadata={},
            )
        ]

    service = IndexService(
        data_dir=data_dir,
        index_dir=index_dir,
        embed_texts=lambda texts: np.ones((len(texts), 3), dtype=np.float32),
        load_paper=load_paper,
    )

    result = service.build()

    assert result.chunk_count == 1
    assert result.embedding_shape == (1, 3)


def test_index_service_default_loader_uses_nutrimaster_chunking(tmp_path: Path):
    from indexing import GeneChunk
    from indexing.index_service import IndexService
    import indexing.index_service as index_service_module
    import inspect

    assert "utils.data_loader" not in inspect.getsource(index_service_module)

    data_dir = tmp_path / "data"
    index_dir = tmp_path / "index"
    data_dir.mkdir()
    index_dir.mkdir()
    json_file = data_dir / "paper_nutri_plant_verified.json"
    json_file.write_text(
        """
        {
          "Title": "Lycopene tomato",
          "Journal": "Plant Cell",
          "DOI": "10.example/lycopene",
          "Common_Genes": [
            {
              "Gene_Name": "PSY1",
              "Species": "Tomato",
              "Summary_Key_Findings_of_Core_Gene": "PSY1 controls carotenoid accumulation in fruit."
            }
          ]
        }
        """,
        encoding="utf-8",
    )
    loaded_chunks = []

    class FakeIndexer:
        def __init__(self, index_dir, data_dir, embed_fn):
            pass

        def build_incremental(self, *, force, load_paper_fn):
            loaded_chunks.extend(load_paper_fn(json_file))
            return loaded_chunks, np.ones((len(loaded_chunks), 3), dtype=np.float32)

    service = IndexService(
        data_dir=data_dir,
        index_dir=index_dir,
        embed_texts=lambda texts: np.ones((len(texts), 3), dtype=np.float32),
        indexer_cls=FakeIndexer,
    )

    result = service.build()

    assert result.chunk_count == 1
    assert isinstance(loaded_chunks[0], GeneChunk)
    assert loaded_chunks[0].gene_name == "PSY1"
