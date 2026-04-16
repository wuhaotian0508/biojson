"""
search 包 — 多来源检索模块

包含:
  - JinaRetriever   : 基因数据库向量检索（Jina Embedding + 余弦相似度）
  - JinaReranker    : 统一候选结果重排序（Jina Reranker API）
  - PersonalLibrary : 用户个人 PDF 知识库（上传、解析、检索）
  - embedding_utils : 共享嵌入向量工具（get_embeddings, get_query_embedding）
"""
from search.retriever import JinaRetriever
from search.personal_lib import PersonalLibrary
from search.reranker import JinaReranker

__all__ = ["JinaRetriever", "PersonalLibrary", "JinaReranker"]
