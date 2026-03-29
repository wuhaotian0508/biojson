"""
构建索引脚本 - 使用简单的 TF-IDF 向量化替代 Jina API
"""
import numpy as np
import pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from data_loader import DataLoader
import config


def build_simple_index():
    """构建简单索引（使用 TF-IDF）"""
    print("构建简单索引（TF-IDF 方法）...")

    # 加载数据
    loader = DataLoader()
    chunks = loader.load_all_genes()

    print(f"为 {len(chunks)} 个 chunk 生成向量...")

    # 使用 TF-IDF 生成向量
    texts = [chunk.content for chunk in chunks]
    vectorizer = TfidfVectorizer(max_features=1024, ngram_range=(1, 2))
    embeddings = vectorizer.fit_transform(texts).toarray()

    print(f"向量维度: {embeddings.shape}")

    # 保存索引
    config.INDEX_DIR.mkdir(parents=True, exist_ok=True)

    with open(config.INDEX_DIR / "chunks.pkl", 'wb') as f:
        pickle.dump(chunks, f)

    np.save(config.INDEX_DIR / "embeddings.npy", embeddings)

    # 保存 vectorizer
    with open(config.INDEX_DIR / "vectorizer.pkl", 'wb') as f:
        pickle.dump(vectorizer, f)

    print(f"索引构建完成，保存到 {config.INDEX_DIR}")
    print(f"- chunks.pkl: {len(chunks)} 个基因")
    print(f"- embeddings.npy: {embeddings.shape}")
    print(f"- vectorizer.pkl: TF-IDF 向量化器")


if __name__ == "__main__":
    build_simple_index()
