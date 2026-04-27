"""
基于 Jina API 的向量检索模块

职责：
  1. 管理基因数据的向量索引（构建 / 加载 / 持久化 / 增量更新）
  2. 提供多种检索模式：
     - 纯稠密向量检索（Dense-only）
     - BM25 + Dense 混合检索（Hybrid）
     - Cross-Encoder 重排序（Rerank）
  3. 查询增强：
     - 查询扩写（双语术语、希腊字母、立体化学描述符）
     - 查询翻译（LLM 提取关键术语并翻译）
  4. 提供查询级嵌入向量（供 PersonalLibrary 等外部模块复用）

索引文件存储在 INDEX_DIR 下：
  - chunks.pkl       — 序列化的 GeneChunk 列表（包含基因元数据）
  - embeddings.npy   — 对应的嵌入向量矩阵 (N, dim)
  - bm25.pkl         — BM25 倒排索引（关键词检索）
  - manifest.json    — 每个 JSON 文件的 sha256 / chunker_version / chunk 区间
  - relations.pkl    — (可选) 结构化关系索引

增量更新机制：
  - 对比磁盘 JSON 的 sha256 与 manifest.json
  - 只对新增 / 修改 / chunker 版本变化的文件重新 embedding
  - 未变化部分复用已有 chunks / embeddings（节省 API 调用）

检索模式对比：
  1. Dense-only（search）：
     - 纯语义相似度，适合改写查询、跨语言查询
     - 对专有名词（基因名、化合物名）召回较弱
  2. Hybrid（hybrid_search）：
     - BM25（关键词） + Dense（语义） RRF 融合
     - 兼顾专有名词和语义理解，推荐使用
  3. Hybrid + Rerank（hybrid_search with rerank=True）：
     - 在 Hybrid 基础上用 Cross-Encoder 精排
     - 最高精度，但 API 调用成本较高

查询增强策略：
  - 规则扩写（expand_query）：
      "α-番茄碱" → "α-番茄碱 α-tomatine alpha-tomatine"
      "25S 构型" → "25S 构型 (25S)- 25S-configured"
  - LLM 翻译（translate_query_terms）：
      "番茄果实中类胡萝卜素的合成途径"
      → "番茄 tomato 果实 fruit 类胡萝卜素 carotenoid 合成途径 biosynthesis pathway"
"""
import pickle
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional

from utils.chunk_types import GeneChunk
from utils.data_loader import DataLoader
from utils.indexer import IncrementalIndexer, logger as indexer_logger
from search.embedding_utils import get_embeddings, get_query_embedding, rerank_documents, _build_headers
from search.bm25_retriever import BM25Retriever, rrf_fuse
from search.query_expander import expand_query
from search.query_translator import translate_query_terms
from core.config import (
    TOP_K_RETRIEVAL, DATA_DIR, INDEX_DIR,
)


class JinaRetriever:
    """
    基于 Jina Embedding 的向量检索器。

    使用流程：
        retriever = JinaRetriever()
        retriever.build_index()              # 自动增量构建 / 加载已有索引
        results = retriever.search(query)    # [(GeneChunk, score), ...]
    """

    def __init__(self, index_path: Optional[Path] = None,
                 data_dir: Optional[Path] = None):
        """
        参数:
            index_path: 索引文件存储目录（默认使用 config.INDEX_DIR）
            data_dir:   数据目录（默认 config.DATA_DIR）
        """
        # ---- 预构建 API 请求头，供 embedding 函数复用 ----
        self._headers = _build_headers()
        # ---- 内存中的索引数据 ----
        self.chunks: List[GeneChunk] = []
        self.embeddings: Optional[np.ndarray] = None
        # ---- 索引存储路径 ----
        self.index_path = index_path or INDEX_DIR
        self.data_dir = data_dir or DATA_DIR
        self.index_path.mkdir(parents=True, exist_ok=True)

        # ---- 增量索引管理器 ----
        self._indexer = IncrementalIndexer(
            index_dir=self.index_path,
            data_dir=self.data_dir,
            embed_fn=self._embed_texts,
        )

        # ---- BM25 检索器（延迟加载）----
        self._bm25: Optional[BM25Retriever] = None

    # ------------------------------------------------------------------
    # embedding 回调
    # ------------------------------------------------------------------
    def _embed_texts(self, texts: List[str]) -> np.ndarray:
        """供 IncrementalIndexer 使用的 embedding 回调。"""
        return get_embeddings(texts, headers=self._headers, show_progress=True)

    # ------------------------------------------------------------------
    # 索引构建与加载
    # ------------------------------------------------------------------
    def build_index(self, data_dir: Path = None, force: bool = False,
                    incremental: bool = True):
        """
        构建或加载向量索引。

        - 默认走增量路径（incremental=True）：对比磁盘 JSON 的 sha256 与
          manifest.json，只对新增 / 修改 / chunker 版本变化的文件重新
          embedding，未变化部分复用已有 chunks / embeddings。
        - force=True：丢弃旧索引全量重建。
        - incremental=False：退化为一次性加载已有 chunks/embeddings
          （只做启动时的监控检查，不重建也不 embedding）。

        参数:
            data_dir:     基因 JSON 数据目录（覆盖 __init__ 时的设置）
            force:        是否强制重建（忽略已有索引）
            incremental:  True = 增量构建；False = 仅加载已有索引
        """
        if data_dir is not None and Path(data_dir) != self.data_dir:
            # 数据目录变更 → 重新创建 indexer
            self.data_dir = Path(data_dir)
            self._indexer = IncrementalIndexer(
                index_dir=self.index_path,
                data_dir=self.data_dir,
                embed_fn=self._embed_texts,
            )

        # 启动监控
        self._indexer.monitor_on_startup()

        if not incremental:
            chunks_file = self.index_path / "chunks.pkl"
            emb_file = self.index_path / "embeddings.npy"
            if chunks_file.exists() and emb_file.exists():
                indexer_logger.info("incremental=False，直接加载已有索引")
                with open(chunks_file, "rb") as f:
                    self.chunks = pickle.load(f)
                self.embeddings = np.load(emb_file)
                indexer_logger.info(f"已加载 {len(self.chunks)} 个 chunk")
                return
            indexer_logger.warning(
                "incremental=False 但索引不存在，fallthrough 到增量构建")

        chunks, embs = self._indexer.build_incremental(
            force=force,
            load_paper_fn=DataLoader(self.data_dir).load_paper,
        )
        self.chunks = chunks
        self.embeddings = embs

    # ------------------------------------------------------------------
    # 检索
    # ------------------------------------------------------------------
    def search(self, query: str, top_k: int = TOP_K_RETRIEVAL,
               chunk_type_filter: Optional[List[str]] = None,
               gene_type_filter: Optional[List[str]] = None
               ) -> List[Tuple[GeneChunk, float]]:
        """
        纯稠密向量检索（Dense-only）：返回与 query 语义最相关的 top_k 个 chunk。

        参数:
            query:              用户查询文本
            top_k:              返回结果数量（默认 config.TOP_K_RETRIEVAL）
            chunk_type_filter:  只保留指定 chunk_type 的结果
                                (e.g. ["pathway_gene","regulation_gene"])
            gene_type_filter:   只保留指定 gene_type 的结果
                                (e.g. ["Pathway_Genes"])

        返回:
            [(GeneChunk, cosine_similarity_score), ...] 按分数降序
            - cosine_similarity_score: 0-1 之间，越高越相关

        工作流程:
            1. 对 query 调用 Jina Embedding API 获取查询向量
            2. 计算查询向量与所有 chunk 向量的余弦相似度
            3. 应用 chunk_type / gene_type 过滤（不符合的设为 -inf）
            4. 排序并返回 top_k 个结果

        适用场景:
            - 语义改写查询（"番茄中控制番茄红素的基因" vs "lycopene biosynthesis in tomato"）
            - 跨语言查询（中文 query 匹配英文 chunk）
            - 概念级检索（"抗旱" 匹配 "drought tolerance"）

        局限性:
            - 对专有名词（基因名、化合物名）召回较弱
            - 推荐使用 hybrid_search() 兼顾关键词和语义
        """
        if self.embeddings is None:
            raise ValueError("Index not built. Call build_index() first.")

        # ---- 查询向量 ----
        query_emb = get_query_embedding(query, headers=self._headers)

        # ---- 余弦相似度 ----
        scores = np.dot(self.embeddings, query_emb) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_emb)
        )

        # ---- 过滤 ----
        valid_mask = np.ones(len(self.chunks), dtype=bool)
        if chunk_type_filter:
            ct = set(chunk_type_filter)
            valid_mask &= np.array([c.chunk_type in ct for c in self.chunks])
        if gene_type_filter:
            gt = set(gene_type_filter)
            valid_mask &= np.array([c.gene_type in gt for c in self.chunks])
        if not valid_mask.all():
            scores = np.where(valid_mask, scores, -np.inf)

        # ---- top-k ----
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = [(self.chunks[i], float(scores[i])) for i in top_indices
                   if scores[i] != -np.inf]
        return results

    def get_query_embedding(self, query: str) -> np.ndarray:
        """获取查询向量（供外部模块使用，如 PersonalLibrary 检索）。"""
        return get_query_embedding(query, headers=self._headers)

    # ------------------------------------------------------------------
    # BM25 + RRF 混合检索
    # ------------------------------------------------------------------
    def _ensure_bm25(self, auto_build: bool = True) -> BM25Retriever:
        """延迟加载 BM25 索引，不存在则基于当前 chunks 构建并持久化。"""
        if self._bm25 is not None:
            return self._bm25
        bm25 = BM25Retriever(index_path=self.index_path)
        if bm25.load():
            # 校验和 chunks 对齐
            if bm25.n_chunks != len(self.chunks):
                indexer_logger.warning(
                    f"bm25.pkl ({bm25.n_chunks}) 与 chunks.pkl "
                    f"({len(self.chunks)}) 数量不一致，重建 BM25 索引")
                bm25 = BM25Retriever(index_path=self.index_path)
                bm25.build(self.chunks)
                bm25.save()
        else:
            if not auto_build:
                raise FileNotFoundError("bm25.pkl 不存在，请先构建")
            indexer_logger.info(
                f"bm25.pkl 不存在，基于 {len(self.chunks)} 个 chunk 构建 BM25 索引 ...")
            bm25.build(self.chunks)
            bm25.save()
            indexer_logger.info(f"BM25 索引已保存至 {self.index_path / 'bm25.pkl'}")
        self._bm25 = bm25
        return bm25

    def build_bm25_index(self, force: bool = False) -> None:
        """显式构建 BM25 索引（一次性操作，无 API 调用）。"""
        if self.chunks is None or len(self.chunks) == 0:
            raise ValueError("chunks 为空，请先调用 build_index() 或加载索引")
        bm25_path = self.index_path / "bm25.pkl"
        if bm25_path.exists() and not force:
            indexer_logger.info(f"bm25.pkl 已存在，跳过（使用 force=True 重建）")
            return
        bm25 = BM25Retriever(index_path=self.index_path)
        bm25.build(self.chunks)
        bm25.save()
        self._bm25 = bm25
        indexer_logger.info(f"BM25 索引完成: {bm25.n_chunks} 个 chunk")

    async def hybrid_search(self, query: str, top_k: int = TOP_K_RETRIEVAL,
                      chunk_type_filter: Optional[List[str]] = None,
                      gene_type_filter: Optional[List[str]] = None,
                      dense_k: int = 100,
                      bm25_k: int = 100,
                      dense_weight: float = 1.0,
                      bm25_weight: float = 1.0,
                      rrf_k: int = 60,
                      rerank: bool = False,
                      rerank_top_n: int = 50,
                      expand_query_variants: bool = True,
                      translate_terms: bool = True,
                      ) -> List[Tuple[GeneChunk, float]]:
        """
        BM25 + 稠密向量的 RRF 混合检索，可选 Cross-Encoder 重排（推荐使用）。

        参数:
            query:            用户查询
            top_k:            最终返回结果数量（默认 config.TOP_K_RETRIEVAL）
            chunk_type_filter / gene_type_filter: 同 search()
            dense_k / bm25_k: 每一路召回的候选数量（候选越多融合越稳，默认各 100）
            dense_weight / bm25_weight: 两路的 RRF 权重（默认 1:1，可调整为 0.7:0.3 等）
            rrf_k:            RRF 平滑常数（默认 60，越大排名衰减越慢）
            rerank:           是否启用 Jina Cross-Encoder 重排（默认 False，开启后精度最高）
            rerank_top_n:     送入 reranker 的候选数量（默认 50；实际取 min(rerank_top_n, RRF结果数)）
            expand_query_variants: 是否对 query 做双语扩写（默认 True，解决中文 query × 英文 chunk 问题）
            translate_terms:  是否用 LLM 补充翻译关键术语（默认 True，在术语表基础上补充）

        返回:
            [(GeneChunk, score), ...] 按分数降序
            - rerank=False: score 为 RRF 融合分数（无量纲，相对值）
            - rerank=True:  score 为 Jina reranker relevance_score（0-1，绝对相关性）

        工作流程:
            0. 查询增强（可选）：
               - translate_terms=True: LLM 提取关键术语并翻译（"番茄" → "番茄 tomato"）
               - expand_query_variants=True: 规则扩写（"α-番茄碱" → "α-番茄碱 α-tomatine alpha-tomatine"）
            1. 稠密召回（Dense）：
               - 对增强后的 query 调用 Jina Embedding API
               - 计算余弦相似度，取 top-dense_k 个候选
            2. 稀疏召回（BM25）：
               - 对所有扩写变体分别做 BM25 检索
               - 合并结果（同一 chunk 取最高分），取 top-bm25_k 个候选
            3. RRF 融合：
               - 对两路召回结果做 Reciprocal Rank Fusion
               - 公式: score(i) = Σ w_l / (k + rank_l(i))
               - 只看排名，不看原始分数（解决量纲不一致问题）
            4a. 不重排（rerank=False）：
               - 直接返回 RRF top-k 结果
            4b. Cross-Encoder 重排（rerank=True）：
               - 取 RRF top-rerank_top_n 候选
               - 调用 Jina Reranker API（Cross-Encoder 模型）
               - 返回重排后的 top-k 结果

        适用场景:
            - 专有名词 + 语义理解（"GAME8 基因在番茄中的功能"）
            - 关键词组合查询（"番茄 + 类胡萝卜素 + 合成"）
            - 跨语言查询（中文 query 匹配英文 chunk）
            - 需要最高精度时开启 rerank=True

        性能考虑:
            - Dense + BM25: 无额外 API 调用（BM25 本地计算）
            - Rerank: 额外 1 次 Jina API 调用（~100ms）
            - 推荐配置: dense_k=100, bm25_k=100, rerank_top_n=50
        """
        if self.embeddings is None:
            raise ValueError("Index not built. Call build_index() first.")

        bm25 = self._ensure_bm25()

        # ---- 过滤 mask ----
        valid_mask = np.ones(len(self.chunks), dtype=bool)
        if chunk_type_filter:
            ct = set(chunk_type_filter)
            valid_mask &= np.array([c.chunk_type in ct for c in self.chunks])
        if gene_type_filter:
            gt = set(gene_type_filter)
            valid_mask &= np.array([c.gene_type in gt for c in self.chunks])
        valid_idx = set(int(i) for i in np.where(valid_mask)[0])

        # ---- 0) 查询增强：LLM 提取关键术语并翻译 ----
        enhanced_query = query
        if translate_terms:
            enhanced_query = await translate_query_terms(query)

        # ---- 1) 稠密召回（使用增强后的 query）----
        query_emb = get_query_embedding(enhanced_query, headers=self._headers)
        scores = np.dot(self.embeddings, query_emb) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_emb)
        )
        if not valid_mask.all():
            scores = np.where(valid_mask, scores, -np.inf)
        dense_top = np.argsort(scores)[::-1][:dense_k]
        dense_ranked: List[Tuple[int, float]] = [
            (int(i), float(scores[i])) for i in dense_top if scores[i] != -np.inf
        ]

        # ---- 2) BM25 召回（支持 query 扩写）----
        if expand_query_variants:
            # 对所有扩写变体做 BM25，合并结果后去重
            variants = expand_query(enhanced_query)
            bm25_all_results: dict[int, float] = {}  # idx -> max_score
            for variant in variants:
                variant_results = bm25.search(variant, top_k=bm25_k * 2)
                for idx, score in variant_results:
                    if idx in valid_idx:
                        bm25_all_results[idx] = max(bm25_all_results.get(idx, 0.0), score)
            # 按分数排序，取 top bm25_k
            bm25_ranked: List[Tuple[int, float]] = sorted(
                bm25_all_results.items(), key=lambda x: x[1], reverse=True
            )[:bm25_k]
        else:
            # 不扩写，直接用增强后的 query
            bm25_raw = bm25.search(enhanced_query, top_k=bm25_k * 2)
            bm25_ranked: List[Tuple[int, float]] = [
                (i, s) for (i, s) in bm25_raw if i in valid_idx
            ][:bm25_k]

        # ---- 3) RRF 融合 ----
        fused = rrf_fuse(dense_ranked, bm25_ranked,
                         k=rrf_k, weights=[dense_weight, bm25_weight])

        # ---- 4a) 不重排：直接截断 top_k ----
        if not rerank:
            top = fused[:top_k]
            return [(self.chunks[i], float(s)) for i, s in top]

        # ---- 4b) Cross-Encoder 重排 ----
        # 取 RRF top-(rerank_top_n) 候选，送 Jina reranker
        candidates = fused[:rerank_top_n]
        candidate_chunks = [self.chunks[i] for i, _ in candidates]
        candidate_texts = [c.content for c in candidate_chunks]

        rerank_results = rerank_documents(
            query=query,
            documents=candidate_texts,
            top_n=top_k,
            headers=self._headers,
        )
        # rerank_results 已按 relevance_score 降序，index 对应 candidate_chunks 中的位置
        return [
            (candidate_chunks[r["index"]], float(r["relevance_score"]))
            for r in rerank_results
        ]


if __name__ == "__main__":
    retriever = JinaRetriever()
    retriever.build_index()

    # 测试检索
    query = "植物抗旱转录因子DREB的调控机制"
    results = retriever.search(query)

    print(f"\nQuery: {query}")
    print(f"Top {len(results)} results:")
    for i, (chunk, score) in enumerate(results, 1):
        print(f"\n{i}. {chunk.gene_name} [{chunk.chunk_type}] - Score: {score:.4f}")
        print(f"   来源: {chunk.paper_title}")
        print(f"   DOI: {chunk.doi}")
