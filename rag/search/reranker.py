"""
统一 Jina Reranker 模块

职责：对多来源合并后的候选结果进行统一重排序。

Pipeline 中的位置：
  PubMed 搜索结果 ─┐
  基因库检索结果   ─┼→ 合并为 all_candidates → JinaReranker.rerank() → 排序后 top_n
  个人库检索结果   ─┘

候选结果使用统一 dict 格式：
  {"source_type": "...", "title": "...", "content": "...", "score": 0.0, "metadata": {...}}
"""
import logging
import time
from typing import List, Dict

import requests

from config import JINA_API_KEY, JINA_RERANK_URL, RERANK_MODEL

logger = logging.getLogger(__name__)


class JinaReranker:
    """
    使用 Jina Reranker API 对统一格式的候选结果列表进行语义重排序。

    与 JinaRetriever 的区别：
    - JinaRetriever: 负责第一阶段的粗排（向量相似度 top-k）
    - JinaReranker:  负责第二阶段的精排（cross-encoder 重排序）

    支持自动重试（指数退避），防止偶发网络错误导致整个 pipeline 失败。
    """

    def __init__(self):
        self._headers = {
            "Authorization": f"Bearer {JINA_API_KEY}",
            "Content-Type": "application/json",
        }

    def rerank(self, query: str, candidates: List[Dict], top_n: int,
               max_retries: int = 3) -> List[Dict]:
        """
        对候选结果进行语义重排序，返回最相关的 top_n 个。

        参数:
            query:       用户查询文本
            candidates:  候选结果列表，每个 dict 至少包含 "content" 字段
            top_n:       返回的最大结果数
            max_retries: 最大重试次数（指数退避：1s, 2s, 3s...）

        返回:
            重排序后的 top_n 个结果，每个 dict 的 "score" 已更新为 relevance_score
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
