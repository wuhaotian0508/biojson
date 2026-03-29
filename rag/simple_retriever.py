"""
简单检索器 - 使用 TF-IDF 替代 Jina API（适合演示和本地测试）
"""
import numpy as np
import pickle
from pathlib import Path
from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from data_loader import GeneChunk, DataLoader
import config


class SimpleRetriever:
    """基于 TF-IDF 的简单检索器"""

    def __init__(self):
        self.top_k = config.TOP_K_RERANK

        self.chunks: List[GeneChunk] = []
        self.embeddings: np.ndarray = None
        self.vectorizer: TfidfVectorizer = None

    def build_index(self, force_rebuild: bool = False):
        """构建索引"""
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
        """检索相关文档"""
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
