"""
检索器 - 使用 Jina Embedding 和 Reranker 进行两阶段检索
"""
import numpy as np
import pickle
from pathlib import Path
from typing import List, Tuple
import requests
from data_loader import GeneChunk, DataLoader
import config


class JinaRetriever:
    """基于 Jina API 的检索器"""

    def __init__(self):
        self.api_key = config.JINA_API_KEY
        self.embedding_model = config.EMBEDDING_MODEL
        self.rerank_model = config.RERANK_MODEL
        self.top_k_retrieval = config.TOP_K_RETRIEVAL
        self.top_k_rerank = config.TOP_K_RERANK

        self.chunks: List[GeneChunk] = []
        self.embeddings: np.ndarray = None

        self.embedding_url = "https://api.jina.ai/v1/embeddings"
        self.rerank_url = "https://api.jina.ai/v1/rerank"

    def build_index(self, force_rebuild: bool = False):
        """构建索引"""
        index_file = config.INDEX_DIR / "chunks.pkl"
        embeddings_file = config.INDEX_DIR / "embeddings.npy"

        # 检查是否已有索引
        if not force_rebuild and index_file.exists() and embeddings_file.exists():
            print("加载已有索引...")
            with open(index_file, 'rb') as f:
                self.chunks = pickle.load(f)
            self.embeddings = np.load(embeddings_file)
            print(f"加载了 {len(self.chunks)} 个 chunk")
            return

        print("构建新索引...")
        # 加载数据
        loader = DataLoader()
        self.chunks = loader.load_all_genes()

        # 生成 embeddings
        print(f"为 {len(self.chunks)} 个 chunk 生成向量...")
        texts = [chunk.content for chunk in self.chunks]

        # 批量生成 embeddings (Jina API 支持批量)
        batch_size = 100
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            print(f"处理 {i+1}-{min(i+batch_size, len(texts))}/{len(texts)}")

            embeddings = self._get_embeddings(batch_texts)
            all_embeddings.extend(embeddings)

        self.embeddings = np.array(all_embeddings)

        # 保存索引
        config.INDEX_DIR.mkdir(parents=True, exist_ok=True)
        with open(index_file, 'wb') as f:
            pickle.dump(self.chunks, f)
        np.save(embeddings_file, self.embeddings)

        print(f"索引构建完成，保存到 {config.INDEX_DIR}")

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """调用 Jina Embedding API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.embedding_model,
            "input": texts,
            "encoding_type": "float"
        }

        response = requests.post(self.embedding_url, json=data, headers=headers)
        response.raise_for_status()

        result = response.json()
        return [item["embedding"] for item in result["data"]]

    def _rerank(self, query: str, candidates: List[str]) -> List[dict]:
        """调用 Jina Reranker API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.rerank_model,
            "query": query,
            "documents": candidates,
            "top_n": self.top_k_rerank
        }

        response = requests.post(self.rerank_url, json=data, headers=headers)
        response.raise_for_status()

        return response.json()["results"]

    def retrieve(self, query: str) -> List[Tuple[GeneChunk, float]]:
        """两阶段检索：向量召回 + Rerank"""
        # 阶段1: 向量检索 top-K
        query_embedding = self._get_embeddings([query])[0]
        query_vec = np.array(query_embedding)

        # 计算余弦相似度
        scores = np.dot(self.embeddings, query_vec) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_vec)
        )

        # 获取 top-K
        top_k_indices = np.argsort(scores)[-self.top_k_retrieval:][::-1]

        # 阶段2: Rerank
        candidates = [self.chunks[i].content for i in top_k_indices]
        rerank_results = self._rerank(query, candidates)

        # 组装结果
        results = []
        for item in rerank_results:
            original_idx = top_k_indices[item["index"]]
            chunk = self.chunks[original_idx]
            score = item["relevance_score"]
            results.append((chunk, score))

        return results


if __name__ == "__main__":
    retriever = JinaRetriever()
    retriever.build_index()

    # 测试检索
    query = "植物中DREB转录因子如何调控抗旱性？"
    results = retriever.retrieve(query)

    print(f"\n查询: {query}")
    print(f"检索到 {len(results)} 个结果:\n")

    for i, (chunk, score) in enumerate(results[:3], 1):
        print(f"{i}. [{chunk.paper_title} | {chunk.gene_name}] (分数: {score:.3f})")
        print(f"   {chunk.content[:200]}...\n")
