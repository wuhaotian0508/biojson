from __future__ import annotations

import time
from typing import Sequence

import numpy as np
import requests

from shared.settings import Settings


def _current_settings():
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


__all__ = ["_build_headers", "_post_with_retry", "get_embeddings", "get_query_embedding", "rerank_documents"]
