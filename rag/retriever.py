"""基于Jina API的向量检索模块"""
import pickle
import requests
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional

from data_loader import GeneChunk, DataLoader
from config import (
    JINA_API_KEY, JINA_EMBEDDING_URL, JINA_RERANK_URL,
    EMBEDDING_MODEL, RERANK_MODEL,
    TOP_K_RETRIEVAL, TOP_K_RERANK, DATA_DIR, INDEX_DIR, require_setting
)

class JinaRetriever:
    """使用Jina API进行向量检索"""

    def __init__(self, index_path: Optional[Path] = None):
        api_key = require_setting("JINA_API_KEY", JINA_API_KEY)
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.chunks: List[GeneChunk] = []
        self.embeddings: Optional[np.ndarray] = None
        self.index_path = index_path or INDEX_DIR
        self.index_path.mkdir(parents=True, exist_ok=True)

    def get_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """调用Jina API获取文本向量"""
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            payload = {
                "model": EMBEDDING_MODEL,
                "input": batch,
                "task": "retrieval.passage"  # 用于文档检索
            }

            resp = requests.post(JINA_EMBEDDING_URL, json=payload, headers=self.headers, timeout=60)
            resp.raise_for_status()

            data = resp.json()
            batch_emb = [item["embedding"] for item in data["data"]]
            all_embeddings.extend(batch_emb)

            print(f"  Embedded {min(i+batch_size, len(texts))}/{len(texts)}")

        return np.array(all_embeddings)

    def get_query_embedding(self, query: str) -> np.ndarray:
        """获取查询向量"""
        payload = {
            "model": EMBEDDING_MODEL,
            "input": [query],
            "task": "retrieval.query"  # 用于查询
        }
        resp = requests.post(JINA_EMBEDDING_URL, json=payload, headers=self.headers, timeout=60)
        resp.raise_for_status()
        return np.array(resp.json()["data"][0]["embedding"])

    def build_index(self, data_dir: Path = DATA_DIR, force: bool = False):
        """构建向量索引"""
        chunks_file = self.index_path / "chunks.pkl"
        emb_file = self.index_path / "embeddings.npy"

        if not force and chunks_file.exists() and emb_file.exists():
            print("Loading existing index...")
            with open(chunks_file, "rb") as f:
                self.chunks = pickle.load(f)
            self.embeddings = np.load(emb_file)
            print(f"Loaded {len(self.chunks)} chunks")
            return

        print("Building new index...")
        loader = DataLoader(data_dir)
        self.chunks = loader.load_all_genes()

        # 获取所有文本的向量
        texts = [c.content for c in self.chunks]
        print(f"Getting embeddings for {len(texts)} chunks...")
        self.embeddings = self.get_embeddings(texts)

        # 保存索引
        with open(chunks_file, "wb") as f:
            pickle.dump(self.chunks, f)
        np.save(emb_file, self.embeddings)
        print(f"Index saved to {self.index_path}")

    def search(self, query: str, top_k: int = TOP_K_RETRIEVAL) -> List[Tuple[GeneChunk, float]]:
        """向量检索"""
        if self.embeddings is None:
            raise ValueError("Index not built. Call build_index() first.")

        # 获取查询向量
        query_emb = self.get_query_embedding(query)

        # 计算余弦相似度
        scores = np.dot(self.embeddings, query_emb) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_emb)
        )

        # 获取top-k
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = [(self.chunks[i], float(scores[i])) for i in top_indices]

        return results

    def rerank(self, query: str, candidates: List[Tuple[GeneChunk, float]],
               top_k: int = TOP_K_RERANK) -> List[Tuple[GeneChunk, float]]:
        """使用Jina Reranker重排序"""
        if not candidates:
            return []

        documents = [c[0].content for c in candidates]

        payload = {
            "model": RERANK_MODEL,
            "query": query,
            "documents": documents,
            "top_n": top_k
        }

        resp = requests.post(JINA_RERANK_URL, json=payload, headers=self.headers, timeout=60)
        resp.raise_for_status()

        results = resp.json()["results"]
        reranked = []
        for item in results:
            idx = item["index"]
            score = item["relevance_score"]
            reranked.append((candidates[idx][0], score))

        return reranked

    def retrieve(self, query: str, use_rerank: bool = True) -> List[Tuple[GeneChunk, float]]:
        """完整检索流程：向量检索 + 可选rerank"""
        # 第一阶段：向量检索
        candidates = self.search(query, top_k=TOP_K_RETRIEVAL)

        if not use_rerank:
            return candidates[:TOP_K_RERANK]

        # 第二阶段：rerank
        return self.rerank(query, candidates, top_k=TOP_K_RERANK)


if __name__ == "__main__":
    retriever = JinaRetriever()
    retriever.build_index()

    # 测试检索
    query = "植物抗旱转录因子DREB的调控机制"
    results = retriever.retrieve(query)

    print(f"\nQuery: {query}")
    print(f"Top {len(results)} results:")
    for i, (chunk, score) in enumerate(results, 1):
        print(f"\n{i}. {chunk.gene_name} ({chunk.species}) - Score: {score:.4f}")
        print(f"   来源: {chunk.article_title}")
        print(f"   DOI: {chunk.doi}")
