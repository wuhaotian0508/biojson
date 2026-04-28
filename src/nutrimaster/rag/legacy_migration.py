from __future__ import annotations

import pickle
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nutrimaster.rag.chunking import GeneChunk


@dataclass(frozen=True)
class LegacyIndexMigrationResult:
    chunk_count: int
    source_index_dir: Path
    target_index_dir: Path
    copied_files: tuple[str, ...]


def _legacy_value(chunk: Any, name: str, default: Any = None) -> Any:
    if isinstance(chunk, dict):
        return chunk.get(name, default)
    return getattr(chunk, name, default)


def convert_legacy_chunk(chunk: Any) -> GeneChunk:
    """Convert a legacy pickle chunk object into the canonical GeneChunk type."""
    return GeneChunk(
        gene_name=_legacy_value(chunk, "gene_name", ""),
        paper_title=_legacy_value(chunk, "paper_title", ""),
        journal=_legacy_value(chunk, "journal", ""),
        doi=_legacy_value(chunk, "doi", ""),
        gene_type=_legacy_value(chunk, "gene_type", ""),
        content=_legacy_value(chunk, "content", ""),
        metadata=dict(_legacy_value(chunk, "metadata", {}) or {}),
        chunk_type=_legacy_value(chunk, "chunk_type", "gene"),
        chunker_version=_legacy_value(chunk, "chunker_version", "v1-legacy"),
        source_fields=list(_legacy_value(chunk, "source_fields", []) or []),
        relations=dict(_legacy_value(chunk, "relations", {}) or {}),
    )


def convert_legacy_chunks(chunks: list[Any]) -> list[GeneChunk]:
    return [convert_legacy_chunk(chunk) for chunk in chunks]


def migrate_legacy_index(
    source_index_dir: Path | str,
    target_index_dir: Path | str,
    *,
    legacy_pythonpath: Path | str | None = None,
) -> LegacyIndexMigrationResult:
    source = Path(source_index_dir)
    target = Path(target_index_dir)
    if legacy_pythonpath is not None:
        legacy_path = str(Path(legacy_pythonpath))
        if legacy_path not in sys.path:
            sys.path.insert(0, legacy_path)

    with (source / "chunks.pkl").open("rb") as file:
        legacy_chunks = pickle.load(file)
    chunks = convert_legacy_chunks(legacy_chunks)

    target.mkdir(parents=True, exist_ok=True)
    with (target / "chunks.pkl").open("wb") as file:
        pickle.dump(chunks, file)

    copied_files: list[str] = []
    for filename in ("embeddings.npy", "manifest.json", "bm25.pkl", "relations.pkl"):
        source_file = source / filename
        if source_file.exists():
            shutil.copy2(source_file, target / filename)
            copied_files.append(filename)

    return LegacyIndexMigrationResult(
        chunk_count=len(chunks),
        source_index_dir=source,
        target_index_dir=target,
        copied_files=tuple(copied_files),
    )


__all__ = [
    "LegacyIndexMigrationResult",
    "convert_legacy_chunk",
    "convert_legacy_chunks",
    "migrate_legacy_index",
]
