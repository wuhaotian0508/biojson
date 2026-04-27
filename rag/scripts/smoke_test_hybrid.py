"""
对比 dense-only、BM25+dense RRF、以及 RRF+Rerank 三种检索模式的效果。

用法:
    python -m scripts.smoke_test_hybrid
"""
import sys
import time
from pathlib import Path


# 目标回归 query：测试 GAME8 是否能命中 top-10
QUERIES = [
    ("番茄和马铃薯主要积累 25S 构型的生物碱（如 α-番茄碱），而茄子则主要积累 "
     "25R 构型的生物碱（如 α-澳洲茄胺），这两种生物碱的生物学功能分别是什么？"
     "由什么基因决定其不同构型形式", "GAME8"),
    ("植物抗旱转录因子DREB的调控机制", None),
    ("番茄类胡萝卜素合成通路关键酶", None),
    ("25S 构型与 25R 构型生物碱差异", "GAME8"),
    ("α-番茄碱与 α-澳洲茄胺的生物学功能", "GAME8"),
]


def print_header(title: str):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def print_results(results, expect_gene, label):
    hit_rank = None
    print(f"\n  --- {label} ---")
    for i, (c, s) in enumerate(results, 1):
        marker = ""
        if expect_gene and expect_gene.lower() in (c.gene_name or "").lower():
            marker = "  ✅ HIT"
            if hit_rank is None:
                hit_rank = i
        gene = (c.gene_name or "")[:24]
        ctype = (c.chunk_type or "")[:22]
        title = (c.paper_title or "")[:55]
        print(f"    {i:2d}. [{ctype:22s}] {gene:24s} "
              f"score={s:.4f} | {title}{marker}")
    if expect_gene:
        if hit_rank:
            print(f"    => {expect_gene} 命中于 rank #{hit_rank}")
        else:
            print(f"    ⚠️  {expect_gene} 未命中 top-10")
    return hit_rank


def main():
    here = Path(__file__).resolve().parent.parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))

    from search.retriever import JinaRetriever

    print("[smoke_test_hybrid] 加载索引 ...")
    t0 = time.time()
    retriever = JinaRetriever()
    # 只加载不重建（incremental=False 会直接读 pkl/npy）
    retriever.build_index(incremental=False)
    print(f"  加载 {len(retriever.chunks)} chunks，"
          f"耗时 {time.time()-t0:.1f}s")

    print("[smoke_test_hybrid] 预热 BM25 ...")
    t0 = time.time()
    retriever._ensure_bm25()
    print(f"  就绪，耗时 {time.time()-t0:.1f}s")

    summary = []  # [(query_short, dense_rank, hybrid_rank, rerank_rank)]

    for q, expect_gene in QUERIES:
        print_header(f"QUERY: {q[:100]}")
        if expect_gene:
            print(f"期望命中基因: {expect_gene}")

        # Dense only
        t0 = time.time()
        dense_results = retriever.search(q, top_k=10)
        t_dense = time.time() - t0
        dense_rank = print_results(
            dense_results, expect_gene,
            f"Dense only (cost {t_dense*1000:.0f} ms)")

        # Hybrid (BM25 + Dense RRF)
        t0 = time.time()
        hybrid_results = retriever.hybrid_search(q, top_k=10, rerank=False)
        t_hybrid = time.time() - t0
        hybrid_rank = print_results(
            hybrid_results, expect_gene,
            f"Hybrid BM25+Dense RRF (cost {t_hybrid*1000:.0f} ms)")

        # Hybrid + Rerank
        t0 = time.time()
        rerank_results = retriever.hybrid_search(q, top_k=10, rerank=True, rerank_top_n=50)
        t_rerank = time.time() - t0
        rerank_rank = print_results(
            rerank_results, expect_gene,
            f"Hybrid + Cross-Encoder Rerank (cost {t_rerank*1000:.0f} ms)")

        if expect_gene:
            summary.append((q[:40], expect_gene, dense_rank, hybrid_rank, rerank_rank))

    # 汇总
    if summary:
        print_header("汇总：hit-rank 对比")
        print(f"{'query':<45s} {'expect':<10s} {'dense':>6s} {'hybrid':>8s} {'rerank':>8s}")
        for qs, eg, dr, hr, rr in summary:
            dr_s = f"#{dr}" if dr else "miss"
            hr_s = f"#{hr}" if hr else "miss"
            rr_s = f"#{rr}" if rr else "miss"
            flag = ""
            if rr and not dr:
                flag = "  ✅ rerank 新命中"
            elif rr and dr and rr < dr:
                flag = "  ↑ rerank 改善"
            elif hr and not dr:
                flag = "  ✅ hybrid 新命中"
            print(f"{qs:<45s} {eg:<10s} {dr_s:>6s} {hr_s:>8s} {rr_s:>8s}{flag}")


if __name__ == "__main__":
    main()
