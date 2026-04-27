"""
BM25 混合检索模块。

职责：
  - 对 chunks 做 BM25 倒排索引
  - 提供关键词检索（中英混合文本 → jieba 分词 + 英文 token + 专有名词保留）
  - 与稠密向量检索结果做 RRF（Reciprocal Rank Fusion）融合

和稠密向量的分工：
  - 稠密向量：捕捉语义、改写、跨语言语义映射
  - BM25：捕捉专有名词（基因名、化合物名、EC 号、缩写），尤其对
    "25S、25R、α-番茄碱、GAME8、CYP72A208" 这类词效果显著

持久化：
  - bm25.pkl : 存 BM25Okapi 对象 + tokenized_corpus
  - 与 chunks.pkl 对齐（长度一致，按同一顺序索引）
"""
from __future__ import annotations

import pickle
import re
import unicodedata
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import numpy as np

try:
    from rank_bm25 import BM25Okapi
except ImportError as e:
    raise ImportError(
        "rank_bm25 未安装，请先 pip install rank_bm25") from e

try:
    import jieba
    jieba.initialize()
    _HAS_JIEBA = True
except Exception:
    _HAS_JIEBA = False


# ============================================================
# Tokenizer
# ============================================================
_ASCII_TOKEN = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._\-/]*"   # 基因名、EC 号、CYP72A208 等保持整体
)
# 单独提取化合物风格 token：α-番茄碱、25S、25R 等
_COMPOUND_TOKEN = re.compile(
    r"[αβγδεζηθικλμνξπρστφχψω\u03b1-\u03c9]?[\-\u2010-\u2015]?[A-Za-z0-9\u4e00-\u9fff]+"
)
# 中文区间
_CN_CHARS = re.compile(r"[\u4e00-\u9fff]+")


def tokenize(text: str) -> List[str]:
    """
    混合语言分词：中英文 + 专有名词保护。

    策略：
      1. 先抽出 ASCII token（保留 GAME8、CYP72A208、EC1.14、25S 等整体）
      2. 抽出希腊字母开头的化合物 token（α-番茄碱、β-胡萝卜素）
      3. 对剩余中文段用 jieba 分词（或 2-gram fallback）
      4. 全部小写（基因名大小写不敏感）
      5. 去重但保序（BM25 允许重复，但去掉完全相同的相邻词）

    示例：
      输入: "番茄中 GAME8 基因调控 α-番茄碱的 25S 构型合成"
      输出: ["番茄", "中", "game8", "基因", "调控", "α-番茄碱", "的", "25s", "构型", "合成"]

    专有名词保护：
      - 基因名：GAME8, CYP72A208, PSY1
      - EC 号：EC1.14.13.127
      - 化合物：α-番茄碱, β-胡萝卜素
      - 立体化学：25S, 25R, (2S,3R)

    为什么需要专有名词保护：
      - 标准分词会把 "GAME8" 拆成 "GAME" + "8"
      - 标准分词会把 "α-番茄碱" 拆成 "α" + "-" + "番茄" + "碱"
      - BM25 需要完整匹配才能正确召回
    """
    if not text:
        return []
    text = unicodedata.normalize("NFKC", text)

    tokens: List[str] = []

    # --- 1. ASCII token（包括数字构型 25S/25R） ---
    ascii_matches = list(_ASCII_TOKEN.finditer(text))
    for m in ascii_matches:
        tokens.append(m.group(0).lower())

    # --- 2. 希腊字母开头的化合物 token（α-番茄碱）---
    for m in re.finditer(r"[\u03b1-\u03c9][\-\u2010-\u2015][A-Za-z0-9\u4e00-\u9fff]+", text):
        tokens.append(m.group(0).lower())

    # --- 3. 中文段交给 jieba ---
    cn_segments = _CN_CHARS.findall(text)
    for seg in cn_segments:
        if _HAS_JIEBA:
            for w in jieba.lcut_for_search(seg):
                w = w.strip()
                if len(w) >= 1:
                    tokens.append(w)
        else:
            # fallback: 按 2-gram 切
            for i in range(len(seg) - 1):
                tokens.append(seg[i:i + 2])

    # --- 4. 去重但保序（BM25 允许重复，但去掉完全相同的相邻） ---
    result = []
    prev = None
    for t in tokens:
        t = t.strip()
        if not t or t == prev:
            continue
        # 过滤无信息符号
        if all(c in ".-_/" for c in t):
            continue
        result.append(t)
        prev = t
    return result


# ============================================================
# BM25 Retriever
# ============================================================
class BM25Retriever:
    """
    BM25 关键词检索器，与 JinaRetriever 使用相同的 chunks.pkl。
    """
    def __init__(self, index_path: Path):
        self.index_path = Path(index_path)
        self.bm25: Optional[BM25Okapi] = None
        self.tokenized: List[List[str]] = []
        self.n_chunks: int = 0

    # ---------- 构建 ----------
    def build(self, chunks: Sequence) -> None:
        """对已有 chunks 建立 BM25 索引。"""
        self.tokenized = [tokenize(c.content) for c in chunks]
        self.bm25 = BM25Okapi(self.tokenized)
        self.n_chunks = len(chunks)

    def save(self) -> None:
        bm25_path = self.index_path / "bm25.pkl"
        bm25_path.parent.mkdir(parents=True, exist_ok=True)
        # 原子写
        tmp = bm25_path.with_suffix(".pkl.tmp")
        with open(tmp, "wb") as f:
            pickle.dump({
                "bm25": self.bm25,
                "tokenized": self.tokenized,
                "n_chunks": self.n_chunks,
            }, f)
        tmp.replace(bm25_path)

    def load(self) -> bool:
        bm25_path = self.index_path / "bm25.pkl"
        if not bm25_path.exists():
            return False
        with open(bm25_path, "rb") as f:
            data = pickle.load(f)
        self.bm25 = data["bm25"]
        self.tokenized = data["tokenized"]
        self.n_chunks = data["n_chunks"]
        return True

    # ---------- 检索 ----------
    def search(self, query: str, top_k: int = 50) -> List[Tuple[int, float]]:
        """
        BM25 关键词检索，返回 [(idx, score), ...]，按分数降序。

        参数:
            query: 用户查询（会自动分词）
            top_k: 返回结果数量（默认 50）

        返回:
            [(chunk_idx, bm25_score), ...] 列表
            - chunk_idx: chunk 在 chunks 列表中的索引
            - bm25_score: BM25 分数（越高越相关，0 表示无匹配）

        工作流程：
            1. 对 query 分词（tokenize）
            2. 计算每个 chunk 的 BM25 分数
            3. 排序并返回 top_k（过滤掉分数为 0 的）

        BM25 分数计算：
            score(D, Q) = Σ_{q∈Q} IDF(q) · (f(q,D) · (k1+1)) / (f(q,D) + k1·(1-b+b·|D|/avgdl))
            - f(q,D): 词 q 在文档 D 中的频率
            - |D|: 文档长度
            - avgdl: 平均文档长度
            - k1, b: 调优参数（默认 k1=1.5, b=0.75）

        适用场景：
            - 专有名词精确匹配（"GAME8", "α-番茄碱", "25S"）
            - 关键词组合查询（"番茄 + 类胡萝卜素 + 合成"）
            - 不适合语义改写查询（推荐用 Dense 或 Hybrid）
        """
        if self.bm25 is None:
            raise ValueError("BM25 index not built")
        q_tokens = tokenize(query)
        if not q_tokens:
            return []
        scores = self.bm25.get_scores(q_tokens)
        top_idx = np.argsort(scores)[::-1][:top_k]
        return [(int(i), float(scores[i])) for i in top_idx if scores[i] > 0]


# ============================================================
# 融合：RRF + 加权
# ============================================================
def rrf_fuse(*ranked_lists: Sequence[Tuple[int, float]],
             k: int = 60,
             weights: Optional[Sequence[float]] = None
             ) -> List[Tuple[int, float]]:
    """
    Reciprocal Rank Fusion（倒数排名融合）— 多路召回结果融合算法。

    公式：
        score(i) = Σ_l  w_l / (k + rank_l(i))
        - rank_l(i): 文档 i 在第 l 路召回中的排名（1-based）
        - w_l: 第 l 路的权重
        - k: 平滑常数（默认 60，越大越平滑）

    参数:
        ranked_lists: 多路召回结果 [(idx, any_score), ...]
                      - 只用 rank（排名），不用 score（原始分数）
                      - 每路结果应按相关性降序排列
        k: RRF 平滑常数（默认 60）
           - k 越大，排名靠后的文档分数衰减越慢
           - k 越小，排名靠前的文档优势越明显
        weights: 每路的权重（默认均等）
                 - 例如 [0.7, 0.3] 表示第一路权重 70%，第二路 30%

    返回:
        [(idx, rrf_score), ...] 按 RRF 分数降序排列

    示例：
        Dense 召回: [(5, 0.9), (3, 0.8), (7, 0.7)]  # idx=5 排名1, idx=3 排名2, idx=7 排名3
        BM25 召回:  [(3, 15.2), (5, 12.1), (9, 10.5)]  # idx=3 排名1, idx=5 排名2, idx=9 排名3

        RRF 融合（k=60, weights=[1.0, 1.0]）:
            idx=5: 1/(60+1) + 1/(60+2) = 0.0164 + 0.0161 = 0.0325
            idx=3: 1/(60+2) + 1/(60+1) = 0.0161 + 0.0164 = 0.0325
            idx=7: 1/(60+3) + 0 = 0.0159
            idx=9: 0 + 1/(60+3) = 0.0159

        最终排序: [(5, 0.0325), (3, 0.0325), (7, 0.0159), (9, 0.0159)]

    为什么用 RRF 而不是分数加权：
        - 不同召回路的分数量纲不同（Dense 是余弦相似度 0-1，BM25 是 0-∞）
        - 直接加权会被高分路主导（如 BM25 分数 15 vs Dense 分数 0.9）
        - RRF 只看排名，天然归一化，更鲁棒
    """
    if not ranked_lists:
        return []
    n_lists = len(ranked_lists)
    if weights is None:
        weights = [1.0] * n_lists
    assert len(weights) == n_lists

    fused: dict[int, float] = {}
    for w, ranked in zip(weights, ranked_lists):
        for rank, (idx, _score) in enumerate(ranked, start=1):
            fused[idx] = fused.get(idx, 0.0) + w / (k + rank)

    items = sorted(fused.items(), key=lambda x: x[1], reverse=True)
    return items
