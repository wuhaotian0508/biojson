"""
简单检索器 — 基于 TF-IDF 的本地检索方案（无需 Jina API）

适用场景：
  - 本地开发/演示（无需 API key）
  - 网络不可用时的降级方案
  - 快速验证数据加载逻辑

与 JinaRetriever 的区别：
  - JinaRetriever: 调用 Jina Embedding API 获取语义向量，效果更好
  - SimpleRetriever: 使用 sklearn TF-IDF 生成稀疏向量，纯本地运行

注意：build_index.py 中的 build_simple_index() 与本类的 build_index()
功能完全重复，建议统一使用本类。
"""
import numpy as np
import pickle
from pathlib import Path
from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils.data_loader import GeneChunk, DataLoader
import core.config as config


class SimpleRetriever:
    """
    基于 TF-IDF 的简单检索器。

    索引文件（存储在 INDEX_DIR 下）：
      - chunks.pkl      — 序列化的 GeneChunk 列表
      - embeddings.npy  — TF-IDF 稀疏矩阵（已转为 dense）
      - vectorizer.pkl  — 拟合后的 TfidfVectorizer（用于查询转换）
    """

    def __init__(self):
        self.top_k = config.TOP_K_RERANK  # 返回的最大结果数

        self.chunks: List[GeneChunk] = []          # 基因 chunk 列表
        self.embeddings: np.ndarray = None          # TF-IDF 向量矩阵 (N, max_features)
        self.vectorizer: TfidfVectorizer = None     # 拟合后的向量化器

    def build_index(self, force_rebuild: bool = False):
        """
        构建或加载 TF-IDF 索引。

        参数:
            force_rebuild: 是否强制重建（忽略已有索引文件）
        """
        index_file = config.INDEX_DIR / "chunks.pkl"
        embeddings_file = config.INDEX_DIR / "embeddings.npy"
        vectorizer_file = config.INDEX_DIR / "vectorizer.pkl"

        # 检查是否已有索引
        if not force_rebuild and all([
            index_file.exists(),
            embeddings_file.exists(),
            vectorizer_file.exists()
        ]):
            print("加载已有索引...")
            with open(index_file, 'rb') as f:
                self.chunks = pickle.load(f)
            self.embeddings = np.load(embeddings_file)
            with open(vectorizer_file, 'rb') as f:
                self.vectorizer = pickle.load(f)
            print(f"加载了 {len(self.chunks)} 个 chunk")
            return

        print("构建新索引...")
        # 加载数据
        loader = DataLoader()
        self.chunks = loader.load_all_genes()

        # 生成 TF-IDF embeddings
        print(f"为 {len(self.chunks)} 个 chunk 生成向量...")
        texts = [chunk.content for chunk in self.chunks]

        self.vectorizer = TfidfVectorizer(
            max_features=1024,
            ngram_range=(1, 2),
            min_df=1
        )
        self.embeddings = self.vectorizer.fit_transform(texts).toarray()

        # 保存索引
        config.INDEX_DIR.mkdir(parents=True, exist_ok=True)
        with open(index_file, 'wb') as f:
            pickle.dump(self.chunks, f)
        np.save(embeddings_file, self.embeddings)
        with open(vectorizer_file, 'wb') as f:
            pickle.dump(self.vectorizer, f)

        print(f"索引构建完成，保存到 {config.INDEX_DIR}")

    def retrieve(self, query: str) -> List[Tuple[GeneChunk, float]]:
        """
        使用 TF-IDF 余弦相似度检索最相关的基因 chunks。

        参数:
            query: 用户查询文本

        返回:
            [(GeneChunk, similarity_score), ...] 按分数降序，最多 top_k 条
        """
        # 将查询转换为向量
        query_vec = self.vectorizer.transform([query]).toarray()[0]

        # 计算余弦相似度
        scores = cosine_similarity([query_vec], self.embeddings)[0]

        # 获取 top-K
        top_k_indices = np.argsort(scores)[-self.top_k:][::-1]

        # 组装结果
        results = []
        for idx in top_k_indices:
            chunk = self.chunks[idx]
            score = float(scores[idx])
            results.append((chunk, score))

        return results


if __name__ == "__main__":
    retriever = SimpleRetriever()
    retriever.build_index()

    # 测试检索
    query = "MYB65 基因的功能是什么？"
    results = retriever.retrieve(query)

    print(f"\n查询: {query}")
    print(f"检索到 {len(results)} 个结果:\n")

    for i, (chunk, score) in enumerate(results[:3], 1):
        print(f"{i}. [{chunk.paper_title} | {chunk.gene_name}] (分数: {score:.3f})")
        print(f"   {chunk.content[:200]}...\n")
