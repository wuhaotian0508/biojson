from __future__ import annotations

import json
import logging
import pickle
import time
from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np
import requests

from nutrimaster.config.settings import Settings
from nutrimaster.rag.gene_index import GeneChunk, IndexService

logger = logging.getLogger(__name__)


def _current_settings() -> Settings:
    settings = Settings.from_env()
    if settings.rag is None:
        raise RuntimeError("RAG settings failed to initialize")
    return settings


def _build_headers(api_key: str | None = None) -> dict:
    settings = _current_settings()
    key = api_key or settings.jina_api_key
    if not key:
        raise RuntimeError("JINA_API_KEY is required")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _post_with_retry(
    url: str,
    payload: dict,
    headers: dict,
    timeout: int = 60,
    max_retries: int = 20,
    post=requests.post,
) -> dict:
    last_exc = None
    for attempt in range(max_retries):
        try:
            response = post(url, json=payload, headers=headers, timeout=timeout)
            if response.status_code == 429:
                time.sleep(min(30, 5 * (attempt + 1)))
                continue
            if response.status_code >= 500:
                raise requests.exceptions.HTTPError(
                    f"server error {response.status_code}: {response.text[:200]}"
                )
            response.raise_for_status()
            return response.json()
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError,
            requests.exceptions.ChunkedEncodingError,
        ) as exc:
            last_exc = exc
            time.sleep(min(2**attempt, 30))
    raise RuntimeError(f"embedding API {max_retries} 次全部失败: {last_exc}")


def get_embeddings(
    texts: Sequence[str],
    batch_size: int = 32,
    headers: dict | None = None,
    show_progress: bool = False,
) -> np.ndarray:
    settings = _current_settings()
    headers = headers or _build_headers()
    embeddings = []
    for start in range(0, len(texts), batch_size):
        batch = list(texts[start:start + batch_size])
        data = _post_with_retry(
            settings.rag.jina_embedding_url,
            {
                "model": settings.rag.embedding_model,
                "input": batch,
                "task": "retrieval.passage",
            },
            headers,
        )
        embeddings.extend(item["embedding"] for item in data["data"])
        if show_progress:
            print(f"  Embedded {min(start + batch_size, len(texts))}/{len(texts)}")
    return np.array(embeddings)


def get_query_embedding(query: str, headers: dict | None = None) -> np.ndarray:
    settings = _current_settings()
    headers = headers or _build_headers()
    data = _post_with_retry(
        settings.rag.jina_embedding_url,
        {
            "model": settings.rag.embedding_model,
            "input": [query],
            "task": "retrieval.query",
        },
        headers,
    )
    return np.array(data["data"][0]["embedding"])


def rerank_documents(
    query: str,
    documents: Sequence[str],
    top_n: int | None = None,
    headers: dict | None = None,
) -> list[dict]:
    settings = _current_settings()
    headers = headers or _build_headers()
    payload = {
        "model": settings.rag.rerank_model,
        "query": query,
        "documents": list(documents),
    }
    if top_n is not None:
        payload["top_n"] = top_n
    return _post_with_retry(settings.rag.jina_rerank_url, payload, headers).get("results", [])


class JinaReranker:
    def __init__(
        self,
        *,
        api_key: str,
        rerank_url: str,
        model: str,
        post_json: Callable[[str, dict, dict, int], dict] | None = None,
    ):
        self.rerank_url = rerank_url
        self.model = model
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self._post_json = post_json or self._default_post_json

    @staticmethod
    def _default_post_json(url: str, payload: dict, headers: dict, timeout: int) -> dict:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()

    def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_n: int,
        max_retries: int = 3,
    ) -> list[dict]:
        if not candidates:
            return []
        payload = {
            "model": self.model,
            "query": query,
            "documents": [candidate["content"] for candidate in candidates],
            "top_n": min(top_n, len(candidates)),
        }
        for attempt in range(1, max_retries + 1):
            try:
                data = self._post_json(self.rerank_url, payload, self._headers, 60)
                ranked = []
                for item in data["results"]:
                    entry = dict(candidates[item["index"]])
                    entry["score"] = item["relevance_score"]
                    ranked.append(entry)
                return ranked
            except Exception as exc:
                logger.warning("Jina rerank attempt %d/%d failed: %s", attempt, max_retries, exc)
                if attempt < max_retries:
                    time.sleep(1 * attempt)
        return candidates[:top_n]


class JinaRetriever:
    def __init__(
        self,
        index_path: Path | None = None,
        data_dir: Path | None = None,
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
        manifest_file = self.index_path / "manifest.json"
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
        if manifest_file.exists():
            try:
                json.loads(manifest_file.read_text(encoding="utf-8"))
            except Exception:
                pass

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
        data = _post_with_retry(self.settings.rag.jina_embedding_url, payload, headers)
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
        data = _post_with_retry(self.settings.rag.jina_embedding_url, payload, headers)
        return np.array([item["embedding"] for item in data["data"]])

    def _headers(self) -> dict:
        if not self.settings.jina_api_key:
            raise RuntimeError("JINA_API_KEY is required")
        return {
            "Authorization": f"Bearer {self.settings.jina_api_key}",
            "Content-Type": "application/json",
        }
