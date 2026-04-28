from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
import requests

from nutrimaster.rag.chunking import GeneChunk
from nutrimaster.rag.index_service import IndexService
from nutrimaster.config.settings import Settings


class JinaRetriever:
    def __init__(
        self,
        index_path: Optional[Path] = None,
        data_dir: Optional[Path] = None,
        *,
        settings: Settings | None = None,
    ):
        self.settings = settings or Settings.from_env()
        rag = self.settings.rag
        if rag is None:
            raise RuntimeError("RAG settings failed to initialize")
        self.index_path = Path(index_path or rag.index_dir)
        self.data_dir = Path(data_dir or rag.data_dir)
        self.index_path.mkdir(parents=True, exist_ok=True)
        self.chunks: list[GeneChunk] = []
        self.embeddings: np.ndarray | None = None
        self.load_error: str | None = None
        self._load_index()

    def build_index(self, data_dir: Path = None, force: bool = False, incremental: bool = True):
        if data_dir is not None:
            self.data_dir = Path(data_dir)
        if incremental:
            service = IndexService(
                data_dir=self.data_dir,
                index_dir=self.index_path,
                embed_texts=self._embed_texts,
            )
            service.build(force=force)
        self._load_index()

    def _load_index(self):
        chunks_file = self.index_path / "chunks.pkl"
        embeddings_file = self.index_path / "embeddings.npy"
        self.load_error = None
        if chunks_file.exists() and embeddings_file.exists():
            try:
                with chunks_file.open("rb") as file:
                    chunks = pickle.load(file)
                embeddings = np.load(embeddings_file)
            except Exception as exc:
                self.chunks = []
                self.embeddings = None
                self.load_error = f"{type(exc).__name__}: {exc}"
                return
            if len(chunks) != embeddings.shape[0]:
                self.chunks = []
                self.embeddings = None
                self.load_error = (
                    f"Index shape mismatch: chunks={len(chunks)} embeddings={embeddings.shape[0]}"
                )
                return
            self.chunks = chunks
            self.embeddings = embeddings
        else:
            self.chunks = []
            self.embeddings = None

    def index_status(self) -> dict:
        chunks_file = self.index_path / "chunks.pkl"
        embeddings_file = self.index_path / "embeddings.npy"
        manifest_file = self.index_path / "manifest.json"
        corpus_files = list(self.data_dir.glob("*.json")) if self.data_dir.exists() else []
        manifest_files = None
        if manifest_file.exists():
            try:
                manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
                manifest_files = len(manifest.get("files", {}))
            except Exception:
                manifest_files = None
        return {
            "data_dir": str(self.data_dir),
            "index_dir": str(self.index_path),
            "corpus_files": len(corpus_files),
            "manifest_files": manifest_files,
            "chunks_loaded": len(self.chunks),
            "embeddings_loaded": 0 if self.embeddings is None else int(self.embeddings.shape[0]),
            "chunks_file_exists": chunks_file.exists(),
            "embeddings_file_exists": embeddings_file.exists(),
            "manifest_file_exists": manifest_file.exists(),
            "load_error": self.load_error,
        }

    def search(
        self,
        query: str,
        top_k: int | None = None,
        chunk_type_filter: list[str] | None = None,
        gene_type_filter: list[str] | None = None,
    ) -> list[tuple[GeneChunk, float]]:
        if self.embeddings is None or not self.chunks:
            self._load_index()
        if self.embeddings is None or not self.chunks:
            return []
        query_embedding = self.get_query_embedding(query)
        similarities = self.embeddings @ query_embedding
        denom = np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        scores = similarities / np.where(denom == 0, 1, denom)
        top_k = top_k or (self.settings.rag.top_k_retrieval if self.settings.rag else 20)
        order = np.argsort(scores)[::-1]
        results = []
        for index in order:
            chunk = self.chunks[int(index)]
            if chunk_type_filter and chunk.chunk_type not in chunk_type_filter:
                continue
            if gene_type_filter and chunk.gene_type not in gene_type_filter:
                continue
            results.append((chunk, float(scores[index])))
            if len(results) >= top_k:
                break
        return results

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 20,
        rerank: bool = True,
        rerank_top_n: int = 50,
    ) -> list[tuple[GeneChunk, float]]:
        return self.search(query, top_k=top_k)

    def get_query_embedding(self, query: str) -> np.ndarray:
        headers = self._headers()
        payload = {
            "model": self.settings.rag.embedding_model if self.settings.rag else "jina-embeddings-v3",
            "input": [query],
            "task": "retrieval.query",
        }
        data = self._post_json(self.settings.rag.jina_embedding_url, payload, headers)
        return np.array(data["data"][0]["embedding"])

    def _embed_texts(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 0), dtype=np.float32)
        headers = self._headers()
        payload = {
            "model": self.settings.rag.embedding_model if self.settings.rag else "jina-embeddings-v3",
            "input": texts,
            "task": "retrieval.passage",
        }
        data = self._post_json(self.settings.rag.jina_embedding_url, payload, headers)
        return np.array([item["embedding"] for item in data["data"]])

    def _headers(self) -> dict:
        if not self.settings.jina_api_key:
            raise RuntimeError("JINA_API_KEY is required")
        return {
            "Authorization": f"Bearer {self.settings.jina_api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _post_json(url: str, payload: dict, headers: dict) -> dict:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()
