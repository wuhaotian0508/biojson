"""
基于已有 chunks.pkl 构建 BM25 索引（一次性操作，无 API 调用）。

用法:
    python -m scripts.build_bm25_index            # 若已有 bm25.pkl 则跳过
    python -m scripts.build_bm25_index --force    # 强制重建
"""
import argparse
import pickle
import sys
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="构建 BM25 索引")
    parser.add_argument("--force", action="store_true", help="强制重建")
    args = parser.parse_args()

    here = Path(__file__).resolve().parent.parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))

    import core.config as config
    from search.bm25_retriever import BM25Retriever

    index_dir = config.INDEX_DIR
    chunks_path = index_dir / "chunks.pkl"
    bm25_path = index_dir / "bm25.pkl"

    if not chunks_path.exists():
        print(f"[build_bm25_index] chunks.pkl 不存在: {chunks_path}")
        sys.exit(1)

    if bm25_path.exists() and not args.force:
        print(f"[build_bm25_index] {bm25_path} 已存在，跳过 "
              f"(使用 --force 强制重建)")
        return

    print(f"[build_bm25_index] 读取 {chunks_path} ...")
    t0 = time.time()
    with open(chunks_path, "rb") as f:
        chunks = pickle.load(f)
    print(f"  加载 {len(chunks)} 个 chunk，耗时 {time.time()-t0:.1f}s")

    print(f"[build_bm25_index] 构建 BM25 倒排索引 ...")
    t0 = time.time()
    bm25 = BM25Retriever(index_path=index_dir)
    bm25.build(chunks)
    print(f"  完成，耗时 {time.time()-t0:.1f}s")

    print(f"[build_bm25_index] 写入 {bm25_path} ...")
    t0 = time.time()
    bm25.save()
    print(f"  写入完成，耗时 {time.time()-t0:.1f}s")
    print(f"\n[build_bm25_index] BM25 索引就绪: {bm25.n_chunks} chunks")


if __name__ == "__main__":
    main()
