"""
共享 Jina Embedding 工具模块

将 JinaRetriever 和 PersonalLibrary 中重复的嵌入向量获取逻辑
抽取到此处，避免两处维护相同的 API 调用代码。

提供两个函数：
  - get_embeddings()       批量获取文档嵌入向量（passage 任务）
  - get_query_embedding()  获取单条查询的嵌入向量（query 任务）
"""
import numpy as np
import requests
from typing import List

from core.config import (
    JINA_API_KEY,
    JINA_EMBEDDING_URL,
    EMBEDDING_MODEL,
    require_setting,
)


def _build_headers() -> dict:
    """构建 Jina API 请求头（含鉴权信息）"""
    api_key = require_setting("JINA_API_KEY", JINA_API_KEY)
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


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

    返回:
        np.ndarray — shape (len(texts), embedding_dim)
    """
    if headers is None:
        headers = _build_headers()

    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        payload = {
            "model": EMBEDDING_MODEL,
            "input": batch,
            "task": "retrieval.passage",  # 文档端嵌入（与 query 端区分）
        }

        resp = requests.post(JINA_EMBEDDING_URL, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()

        batch_emb = [item["embedding"] for item in resp.json()["data"]]
        all_embeddings.extend(batch_emb)

        if show_progress:
            print(f"  Embedded {min(i + batch_size, len(texts))}/{len(texts)}")

    return np.array(all_embeddings)


def get_query_embedding(query: str, headers: dict = None) -> np.ndarray:
    """
    获取单条查询的嵌入向量。

    使用 Jina 的 retrieval.query 任务类型，与 get_embeddings() 的
    retrieval.passage 任务类型配对使用，可提升检索精度。

    参数:
        query:   查询文本
        headers: 自定义请求头（为 None 时自动构建）

    返回:
        np.ndarray — shape (embedding_dim,)
    """
    if headers is None:
        headers = _build_headers()

    payload = {
        "model": EMBEDDING_MODEL,
        "input": [query],
        "task": "retrieval.query",  # 查询端嵌入（与 passage 端配对）
    }
    resp = requests.post(JINA_EMBEDDING_URL, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    return np.array(resp.json()["data"][0]["embedding"])
