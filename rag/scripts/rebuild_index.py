"""
重建向量索引 — 命令行入口。

用法:
    # 增量（推荐）：只对新增/修改/版本变化的 JSON 做 embedding
    python -m scripts.rebuild_index

    # 强制全量重建：清空旧 chunks 与 embeddings
    python -m scripts.rebuild_index --force

    # 仅监控不构建
    python -m scripts.rebuild_index --monitor-only

    # Pilot 模式：只处理前 N 个文件（估算成本用）
    python -m scripts.rebuild_index --pilot 100

    # 完成后立即跑目标 query 验证
    python -m scripts.rebuild_index --smoke-test
"""
import argparse
import logging
import sys
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="重建 / 增量更新向量索引")
    parser.add_argument("--force", action="store_true",
                        help="丢弃旧索引全量重建")
    parser.add_argument("--monitor-only", action="store_true",
                        help="只做一致性监控，不重建")
    parser.add_argument("--pilot", type=int, default=0,
                        help="只处理前 N 个 JSON（pilot 模式）")
    parser.add_argument("--data-dir", type=Path, default=None,
                        help="覆盖默认的 DATA_DIR")
    parser.add_argument("--smoke-test", action="store_true",
                        help="构建完成后跑一组目标 query 验证召回")
    parser.add_argument("--log-file", type=Path, default=None,
                        help="把日志同时写入指定文件（默认 rag/logs/rebuild.log）")
    args = parser.parse_args()

    # ---- 插入 rag/ 到 sys.path（允许从任意目录执行）----
    here = Path(__file__).resolve().parent.parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))

    # ---- 同时写文件日志 ----
    log_file = args.log_file or (here / "logs" / "rebuild.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_h = logging.FileHandler(log_file, encoding="utf-8")
    file_h.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
    logging.getLogger("rag.indexer").addHandler(file_h)
    logging.getLogger().addHandler(file_h)
    # 同时也 tee 到 stdout（print 会自动进）
    print(f"[rebuild_index] 日志文件: {log_file}", flush=True)

    import core.config as config
    from search.retriever import JinaRetriever
    from utils.indexer import IncrementalIndexer
    from utils.data_loader import DataLoader

    data_dir = args.data_dir or config.DATA_DIR
    index_dir = config.INDEX_DIR

    retriever = JinaRetriever(index_path=index_dir, data_dir=data_dir)

    if args.monitor_only:
        retriever._indexer.monitor_on_startup()
        return

    if args.pilot > 0:
        # Pilot: 只挑前 N 个文件
        all_files = sorted(data_dir.glob("*_nutri_plant_verified.json"))[: args.pilot]
        print(f"[pilot] 仅处理 {len(all_files)} 个文件")
        # 拷贝到临时目录？直接构造 subset dataloader 更简洁
        loader = DataLoader(data_dir)
        subset_load = loader.load_paper

        # 猴补丁：临时把 data_dir glob 结果限制
        class _PilotIndexer(IncrementalIndexer):
            def build_incremental(self, **kw):
                # 覆盖 all_files
                orig_glob = self.data_dir.glob
                self.data_dir.glob = lambda _pat: iter(all_files)
                try:
                    return super().build_incremental(**kw)
                finally:
                    self.data_dir.glob = orig_glob

        idx = _PilotIndexer(index_dir, data_dir,
                            embed_fn=retriever._embed_texts)
        idx.monitor_on_startup()
        idx.build_incremental(force=args.force, load_paper_fn=subset_load)
        return

    retriever.build_index(force=args.force, incremental=True)
    print("\n完成。可用 retriever.search(query) 做冒烟测试。", flush=True)

    if args.smoke_test:
        _run_smoke_test(retriever)


def _run_smoke_test(retriever):
    """预置的回归 query 集，打印 top-10 结果，用于快速验证重建效果。"""
    queries = [
        # 目标诊断 query
        ("番茄和马铃薯主要积累 25S 构型的生物碱（如 α-番茄碱），而茄子则主要积累 25R 构型的生物碱（如 α-澳洲茄胺），这两种生物碱的生物学功能分别是什么？由什么基因决定其不同构型形式",
         "GAME8"),
        # 其它代表性查询
        ("植物抗旱转录因子DREB的调控机制", None),
        ("番茄类胡萝卜素合成通路关键酶", None),
    ]
    print("\n" + "=" * 80)
    print("SMOKE TEST — 召回验证")
    print("=" * 80)
    for q, expect_gene in queries:
        print(f"\nQuery: {q[:80]}...")
        results = retriever.search(q, top_k=10)
        hit_rank = None
        for i, (c, s) in enumerate(results, 1):
            marker = ""
            if expect_gene and expect_gene.lower() in (c.gene_name or "").lower():
                marker = "  ✅ HIT"
                if hit_rank is None:
                    hit_rank = i
            print(f"  {i:2d}. [{c.chunk_type:22s}] {c.gene_name[:40]:40s}"
                  f" score={s:.4f} | {c.paper_title[:50]}{marker}")
        if expect_gene:
            if hit_rank:
                print(f"  => {expect_gene} 命中于 rank #{hit_rank}")
            else:
                print(f"  ⚠️  未命中 {expect_gene}（rank #11+）")


if __name__ == "__main__":
    main()
