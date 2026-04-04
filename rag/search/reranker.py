"""统一 Jina Reranker 模块"""
import logging
import time
from typing import List, Dict

import requests

from config import JINA_API_KEY, JINA_RERANK_URL, RERANK_MODEL

logger = logging.getLogger(__name__)


class JinaReranker:
    """使用 Jina Reranker 对统一 dict 列表重排序"""

    def __init__(self):
        self._headers = {
            "Authorization": f"Bearer {JINA_API_KEY}",
            "Content-Type": "application/json",
        }

    def rerank(self, query: str, candidates: List[Dict], top_n: int,
               max_retries: int = 3) -> List[Dict]:
        """对 candidates 重排序，返回 top_n 个结果。

        每个 candidate 至少包含 "content" 字段。
        """
        if not candidates:
            return []

        documents = [c["content"] for c in candidates]
        payload = {
            "model": RERANK_MODEL,
            "query": query,
            "documents": documents,
            "top_n": min(top_n, len(candidates)),
        }

        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.post(
                    JINA_RERANK_URL, json=payload,
                    headers=self._headers, timeout=60,
                )
                resp.raise_for_status()
                reranked = []
                for item in resp.json()["results"]:
                    idx = item["index"]
                    entry = dict(candidates[idx])
                    entry["score"] = item["relevance_score"]
                    reranked.append(entry)
                return reranked
            except Exception as e:
                logger.warning("Jina rerank attempt %d/%d failed: %s",
                               attempt, max_retries, e)
                if attempt < max_retries:
                    time.sleep(1 * attempt)

        logger.warning("Jina rerank exhausted retries, returning original order")
        return candidates[:top_n]
