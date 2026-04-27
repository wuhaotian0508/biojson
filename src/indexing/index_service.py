from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from indexing.chunking import chunk_paper
from indexing.incremental_indexer import IncrementalIndexer


@dataclass(frozen=True)
class IndexBuildResult:
    """Summary returned by the index service after a build."""

    chunk_count: int
    embedding_shape: tuple[int, ...] | None
    data_dir: Path
    index_dir: Path


class IndexService:
    """Canonical indexing boundary while legacy RAG modules are being strangled."""

    def __init__(
        self,
        *,
        data_dir: Path,
        index_dir: Path,
        embed_texts: Callable[[list[str]], np.ndarray],
        load_paper: Callable[[Path], list[Any]] | None = None,
        indexer_cls: type | None = None,
    ):
        self.data_dir = Path(data_dir)
        self.index_dir = Path(index_dir)
        self.embed_texts = embed_texts
        self.load_paper = load_paper
        self.indexer_cls = indexer_cls

    def build(self, *, force: bool = False) -> IndexBuildResult:
        indexer_cls = self.indexer_cls or IncrementalIndexer
        load_paper = self.load_paper or self._load_paper_chunks

        indexer = indexer_cls(
            index_dir=self.index_dir,
            data_dir=self.data_dir,
            embed_fn=self.embed_texts,
        )
        chunks, embeddings = indexer.build_incremental(
            force=force,
            load_paper_fn=load_paper,
        )
        return IndexBuildResult(
            chunk_count=len(chunks),
            embedding_shape=None if embeddings is None else tuple(embeddings.shape),
            data_dir=self.data_dir,
            index_dir=self.index_dir,
        )

    @staticmethod
    def _load_paper_chunks(path: Path) -> list[Any]:
        with Path(path).open("r", encoding="utf-8") as file:
            paper = json.load(file)
        return chunk_paper(paper)
