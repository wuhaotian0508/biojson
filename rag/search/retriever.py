"""
基于 Jina API 的向量检索模块

职责：
  - 管理基因数据的向量索引（构建 / 加载 / 持久化）
  - 基于余弦相似度进行 top-k 向量检索
  - 提供查询级嵌入向量（供 PersonalLibrary 等外部模块复用）

索引文件存储在 INDEX_DIR 下：
  - chunks.pkl       — 序列化的 GeneChunk 列表
  - embeddings.npy   — 对应的嵌入向量矩阵 (N, dim)
"""
import pickle
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional

from utils.data_loader import GeneChunk, DataLoader
from search.embedding_utils import get_embeddings, get_query_embedding, _build_headers
from core.config import (
    TOP_K_RETRIEVAL, DATA_DIR, INDEX_DIR,
)


class JinaRetriever:
    """
    基于 Jina Embedding 的向量检索器。

    使用流程：
        retriever = JinaRetriever()
        retriever.build_index()              # 首次构建或加载已有索引
        results = retriever.search(query)    # [(GeneChunk, score), ...]
    """

    def __init__(self, index_path: Optional[Path] = None):
        """
        参数:
            index_path: 索引文件存储目录（默认使用 config.INDEX_DIR）
        """
        # ---- 预构建 API 请求头，供 embedding 函数复用 ----
        self._headers = _build_headers()
        # ---- 内存中的索引数据 ----
        self.chunks: List[GeneChunk] = []               # 所有基因 chunk
        self.embeddings: Optional[np.ndarray] = None     # 对应的嵌入矩阵 (N, dim)
        # ---- 索引存储路径 ----
        self.index_path = index_path or INDEX_DIR
        self.index_path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 索引构建与加载
    # ------------------------------------------------------------------
    def build_index(self, data_dir: Path = DATA_DIR, force: bool = False):
        """
        构建或加载向量索引。

        若索引文件已存在且 force=False，直接从磁盘加载；
        否则从 data_dir 读取 JSON 文件，生成嵌入向量并持久化。

        参数:
            data_dir: 基因 JSON 数据目录
            force:    是否强制重建（忽略已有索引）
        """
        chunks_file = self.index_path / "chunks.pkl"
        emb_file = self.index_path / "embeddings.npy"

        # ---- 尝试加载已有索引 ----
        if not force and chunks_file.exists() and emb_file.exists():
            print("Loading existing index...")
            with open(chunks_file, "rb") as f:
                self.chunks = pickle.load(f)
            self.embeddings = np.load(emb_file)
            print(f"Loaded {len(self.chunks)} chunks")
            return

        # ---- 从数据文件重新构建索引 ----
        print("Building new index...")
        loader = DataLoader(data_dir)
        self.chunks = loader.load_all_genes()

        texts = [c.content for c in self.chunks]
        print(f"Getting embeddings for {len(texts)} chunks...")
        self.embeddings = get_embeddings(texts, headers=self._headers, show_progress=True)

        # ---- 持久化到磁盘 ----
        with open(chunks_file, "wb") as f:
            pickle.dump(self.chunks, f)
        np.save(emb_file, self.embeddings)
        print(f"Index saved to {self.index_path}")

    # ------------------------------------------------------------------
    # 检索
    # ------------------------------------------------------------------
    def search(self, query: str, top_k: int = TOP_K_RETRIEVAL) -> List[Tuple[GeneChunk, float]]:
        """
        向量相似度检索：返回与 query 最相关的 top_k 个基因 chunk。

        参数:
            query: 用户查询文本
            top_k: 返回结果数量

        返回:
            [(GeneChunk, cosine_similarity_score), ...] 按分数降序排列
        """
        if self.embeddings is None:
            raise ValueError("Index not built. Call build_index() first.")

        # ---- 获取查询向量 ----
        query_emb = get_query_embedding(query, headers=self._headers)

        # ---- 计算余弦相似度 ----
        # scores[i] = cos(query_emb, embeddings[i])
        scores = np.dot(self.embeddings, query_emb) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_emb)
        )

        # ---- 取 top-k 并按分数降序排列 ----
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = [(self.chunks[i], float(scores[i])) for i in top_indices]

        return results

    def get_query_embedding(self, query: str) -> np.ndarray:
        """
        获取查询向量（供外部模块使用，如 PersonalLibrary 检索）。

        参数:
            query: 查询文本

        返回:
            np.ndarray — shape (embedding_dim,)
        """
        return get_query_embedding(query, headers=self._headers)


if __name__ == "__main__":
    retriever = JinaRetriever()
    retriever.build_index()

    # 测试检索
    query = "植物抗旱转录因子DREB的调控机制"
    results = retriever.search(query)

    print(f"\nQuery: {query}")
    print(f"Top {len(results)} results:")
    for i, (chunk, score) in enumerate(results, 1):
        print(f"\n{i}. {chunk.gene_name} - Score: {score:.4f}")
        print(f"   来源: {chunk.paper_title}")
        print(f"   DOI: {chunk.doi}")
