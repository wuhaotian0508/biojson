from __future__ import annotations

import hashlib
import json
import logging
import pickle
from pathlib import Path
from typing import Callable

import numpy as np

from indexing.chunking import CHUNKER_VERSION, GeneChunk, chunk_paper

logger = logging.getLogger("indexer")


def sha256_of(path: Path, buf_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        while chunk := file.read(buf_size):
            digest.update(chunk)
    return digest.hexdigest()


class IncrementalIndexer:
    def __init__(
        self,
        index_dir: Path,
        data_dir: Path,
        embed_fn: Callable[[list[str]], np.ndarray],
        file_pattern: str = "*_nutri_plant_verified.json",
    ):
        self.index_dir = Path(index_dir)
        self.data_dir = Path(data_dir)
        self.embed_fn = embed_fn
        self.file_pattern = file_pattern
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_path = self.index_dir / "chunks.pkl"
        self.embeds_path = self.index_dir / "embeddings.npy"
        self.manifest_path = self.index_dir / "manifest.json"

    def monitor_on_startup(self):
        logger.info(
            "[monitor] data_dir=%s verified JSON=%d",
            self.data_dir,
            len(list(self.data_dir.glob(self.file_pattern))),
        )

    def build_incremental(self, *, force: bool = False, batch_embed_size: int = 32, load_paper_fn=None):
        load_paper_fn = load_paper_fn or self._load_paper
        files = sorted(self.data_dir.glob(self.file_pattern))
        manifest = {} if force else self._load_manifest()
        old_chunks, old_embeddings = ([], None) if force else self._load_existing()
        if not self._manifest_reusable(manifest, old_chunks, old_embeddings):
            manifest = {}
            old_chunks, old_embeddings = [], None

        file_shas = {path.name: sha256_of(path) for path in files}
        to_keep = []
        to_rebuild = []
        for path in files:
            entry = manifest.get(path.name)
            if (
                entry
                and entry.get("sha") == file_shas[path.name]
                and entry.get("chunker_version") == CHUNKER_VERSION
            ):
                to_keep.append(path.name)
            else:
                to_rebuild.append(path)

        final_chunks: list[GeneChunk] = []
        final_embedding_parts = []
        new_manifest = {}
        cursor = 0

        for name in to_keep:
            entry = manifest[name]
            start = int(entry["start"])
            end = int(entry["end"])
            chunks = old_chunks[start:end]
            final_chunks.extend(chunks)
            if old_embeddings is not None:
                final_embedding_parts.append(old_embeddings[start:end])
            new_manifest[name] = {
                "sha": entry["sha"],
                "chunker_version": CHUNKER_VERSION,
                "n_chunks": len(chunks),
                "start": cursor,
                "end": cursor + len(chunks),
            }
            cursor += len(chunks)

        for path in to_rebuild:
            chunks = load_paper_fn(path) or []
            embeddings = self.embed_fn([chunk.content for chunk in chunks]) if chunks else None
            if embeddings is not None and embeddings.shape[0] != len(chunks):
                raise RuntimeError("embedding count does not match chunk count")
            start = cursor
            final_chunks.extend(chunks)
            cursor += len(chunks)
            if embeddings is not None:
                final_embedding_parts.append(embeddings)
            new_manifest[path.name] = {
                "sha": file_shas[path.name],
                "chunker_version": CHUNKER_VERSION,
                "n_chunks": len(chunks),
                "start": start,
                "end": cursor,
            }

        final_embeddings = None
        if final_embedding_parts:
            final_embeddings = (
                np.concatenate(final_embedding_parts, axis=0)
                if len(final_embedding_parts) > 1
                else final_embedding_parts[0]
            )
        if final_chunks and final_embeddings is None:
            raise RuntimeError("chunks exist but embeddings are missing")
        if final_embeddings is not None and final_embeddings.shape[0] != len(final_chunks):
            raise RuntimeError("final embeddings do not match chunks")

        self._save(final_chunks, final_embeddings, new_manifest)
        return final_chunks, final_embeddings

    def _load_paper(self, path: Path) -> list[GeneChunk]:
        return chunk_paper(json.loads(Path(path).read_text(encoding="utf-8")))

    def _load_manifest(self) -> dict:
        if not self.manifest_path.exists():
            return {}
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            if data.get("chunker_version") != CHUNKER_VERSION:
                return {}
            return data.get("files", {})
        except Exception:
            return {}

    def _load_existing(self):
        if not (self.chunks_path.exists() and self.embeds_path.exists()):
            return [], None
        try:
            with self.chunks_path.open("rb") as file:
                chunks = pickle.load(file)
            embeddings = np.load(self.embeds_path)
            if len(chunks) != embeddings.shape[0]:
                return [], None
            return chunks, embeddings
        except Exception:
            return [], None

    @staticmethod
    def _manifest_reusable(manifest: dict, chunks: list, embeddings) -> bool:
        if not manifest:
            return True
        if embeddings is None:
            return False
        expected_total = 0
        for entry in manifest.values():
            start = int(entry.get("start", -1))
            end = int(entry.get("end", -1))
            n_chunks = int(entry.get("n_chunks", end - start))
            if start < 0 or end < start or n_chunks != end - start:
                return False
            expected_total = max(expected_total, end)
        return len(chunks) >= expected_total and embeddings.shape[0] >= expected_total

    def _save(self, chunks: list[GeneChunk], embeddings, manifest_files: dict):
        with self.chunks_path.open("wb") as file:
            pickle.dump(chunks, file)
        if embeddings is not None:
            np.save(self.embeds_path, embeddings)
        self.manifest_path.write_text(
            json.dumps(
                {"chunker_version": CHUNKER_VERSION, "files": manifest_files},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


__all__ = ["IncrementalIndexer", "logger", "sha256_of"]
