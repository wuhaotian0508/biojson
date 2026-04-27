from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

import requests

logger = logging.getLogger(__name__)


def _default_post_json(url: str, payload: dict, headers: dict, timeout: int) -> dict:
    response = requests.post(url, json=payload, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()


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
        self._post_json = post_json or _default_post_json

    def rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        top_n: int,
        max_retries: int = 3,
    ) -> list[dict[str, Any]]:
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
