"""
共享 Jina Embedding 工具模块

将 JinaRetriever 和 PersonalLibrary 中重复的嵌入向量获取逻辑
抽取到此处，避免两处维护相同的 API 调用代码。

提供两个函数：
  - get_embeddings()       批量获取文档嵌入向量（passage 任务）
  - get_query_embedding()  获取单条查询的嵌入向量（query 任务）
"""
import time
import numpy as np
import requests
from typing import List

from core.config import (
    JINA_API_KEY,
    JINA_EMBEDDING_URL,
    JINA_RERANK_URL,
    EMBEDDING_MODEL,
    RERANK_MODEL,
    require_setting,
)


def _build_headers() -> dict:
    """构建 Jina API 请求头（含鉴权信息）"""
    api_key = require_setting("JINA_API_KEY", JINA_API_KEY)
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _post_with_retry(url: str, payload: dict, headers: dict,
                     timeout: int = 60, max_retries: int = 20) -> dict:
    """
    带指数退避的 POST。TLS/ConnectionReset 等网络错误自动重试。
    失败退避: 1, 2, 4, 8, 16, 30, 30, ..., 30 秒。
    """
    last_exc = None
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
            if resp.status_code == 429:
                # rate limit: 更长退避
                sleep = min(30, 5 * (attempt + 1))
                print(f"  [embed-retry {attempt+1}/{max_retries}] "
                      f"rate-limited (429); sleep {sleep}s", flush=True)
                time.sleep(sleep)
                continue
            if resp.status_code >= 500:
                raise requests.exceptions.HTTPError(
                    f"server error {resp.status_code}: {resp.text[:200]}")
            resp.raise_for_status()
            return resp.json()
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.HTTPError,
                requests.exceptions.ChunkedEncodingError) as e:
            last_exc = e
            sleep = min(2 ** attempt, 30)
            print(f"  [embed-retry {attempt+1}/{max_retries}] "
                  f"{type(e).__name__}: {e}; sleep {sleep}s", flush=True)
            time.sleep(sleep)
    raise RuntimeError(f"embedding API {max_retries} 次全部失败: {last_exc}")


def get_embeddings(
    texts: List[str],
    batch_size: int = 32,
    headers: dict = None,
    show_progress: bool = False,
) -> np.ndarray:
    """
    批量调用 Jina Embedding API 获取文档向量。

    参数:
        texts:          待嵌入的文本列表
        batch_size:     每次 API 请求的文本数量（默认 32，Jina 单次上限）
        headers:        自定义请求头（为 None 时自动构建）
        show_progress:  是否打印进度信息
    """
    if headers is None:
        headers = _build_headers()

    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        payload = {
            "model": EMBEDDING_MODEL,
            "input": batch,
            "task": "retrieval.passage",
        }
        data = _post_with_retry(JINA_EMBEDDING_URL, payload, headers, timeout=60)
        batch_emb = [item["embedding"] for item in data["data"]]
        all_embeddings.extend(batch_emb)
        if show_progress:
            print(f"  Embedded {min(i + batch_size, len(texts))}/{len(texts)}")
    return np.array(all_embeddings)


def get_query_embedding(query: str, headers: dict = None) -> np.ndarray:
    """获取单条查询的嵌入向量（retrieval.query 任务）。"""
    if headers is None:
        headers = _build_headers()
    payload = {
        "model": EMBEDDING_MODEL,
        "input": [query],
        "task": "retrieval.query",
    }
    data = _post_with_retry(JINA_EMBEDDING_URL, payload, headers, timeout=60)
    return np.array(data["data"][0]["embedding"])


def rerank_documents(
    query: str,
    documents: List[str],
    top_n: int = None,
    headers: dict = None,
) -> List[dict]:
    """
    使用 Jina Reranker API 对候选文档重排序。

    参数:
        query:      用户查询
        documents:  候选文档列表（文本内容）
        top_n:      返回前 N 个结果（None = 返回全部）
        headers:    自定义请求头（为 None 时自动构建）

    返回:
        排序后的结果列表，每项包含:
          - index: 原文档在 documents 中的索引
          - relevance_score: 相关性分数（0-1）
          - document: 原文档内容
    """
    if headers is None:
        headers = _build_headers()

    payload = {
        "model": RERANK_MODEL,
        "query": query,
        "documents": documents,
    }
    if top_n is not None:
        payload["top_n"] = top_n

    data = _post_with_retry(JINA_RERANK_URL, payload, headers, timeout=60)
    return data.get("results", [])
