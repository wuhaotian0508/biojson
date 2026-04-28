"""
pipeline.py — Orchestrator with paper-level parallel processing.

Each paper goes through:
    API #1: extract_all_genes  → Title/Journal/DOI + gene arrays + gene_dict
    API #2+: verify_all_genes  → verification + corrections (batched per 10 genes)

Papers are processed in parallel using ThreadPoolExecutor.

Usage:
    python -m extractor.pipeline               # full pipeline
    python -m extractor.pipeline --test 1      # test: first file
    python -m extractor.pipeline --test name   # test: match filename
    python -m extractor.pipeline --workers 5   # custom parallelism

[PR 改动 by 学长 muskliu - 2026-03-29]
- 提取 collect_paper_result() 函数：将结果按 processed/skipped/failed 分桶，减少 main() 中的重复逻辑
- 提取 _print_paper_result() 函数：顺序和并行模式共用打印逻辑
- 删除未使用的 import sys
- 从 utils.py 导入 GENE_ARRAY_KEY_NAMES 替代硬编码
- main() 中使用新提取的函数，代码更简洁
"""

import argparse
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from .config import (
    MODEL, INPUT_DIR, TOKEN_USAGE_DIR, MAX_WORKERS,
    ensure_dirs,
)
from .extract import extract_paper
from .utils import GENE_ARRAY_KEY_NAMES
from .verify import verify_paper
from .token_tracker import TokenTracker


def collect_paper_result(filename: str, result: dict, all_reports: list,
                         failed_files: list, skipped_files: list):
    """把单篇论文的处理结果分桶收集。

    [PR 新增函数] 原来这段逻辑在 main() 的顺序和并行两处重复写，
    现在提取为独立函数，按 status 分到 all_reports / skipped / failed 三个列表。
    """
    status = result.get("status", "failed")
    if status == "processed":
        report = result.get("report")
        if report:
            all_reports.append(report)
    elif status == "skipped":
        skipped_files.append(filename)
    else:
        failed_files.append(filename)


def resolve_test_files(files: list, test_index: str) -> list:
    """测试模式下筛选文件。

    支持两种方式：
    - 数字索引：--test 1 → 第1个文件
    - 文件名匹配：--test Butelli → 模糊匹配含 "Butelli" 的文件
    """
    if test_index.isdigit():
        idx = int(test_index) - 1
        if 0 <= idx < len(files):
            print(f"🧪 Test mode: file #{idx + 1} → {files[idx]}")
            return [files[idx]]
        print(f"❌ Index {idx + 1} out of range ({len(files)} files)")
        return []
    target = test_index if test_index.endswith(".md") else test_index + ".md"
    matched = [f for f in files if f == target]
    if matched:
        print(f"🧪 Test mode: exact match → {matched[0]}")
        return matched
    matched = [f for f in files if test_index in f]
    if matched:
        print(f"🧪 Test mode: fuzzy match → {matched[0]}")
        return [matched[0]]
    print(f"❌ No match for '{test_index}' ({len(files)} files)")
    return []


def _print_paper_result(stem: str, result: dict):
    """打印单篇论文的处理结果摘要（顺序和并行模式共用）。

    [PR 新增函数] 原来顺序和并行模式各自写了一遍打印逻辑，现在统一。
    显示 fidelity 准确率和 corrections 修正数。
    """
    status = result.get("status")
    if status == "processed":
        report_data = result["report"]
        s = report_data["summary"]
        if s["total_fields"] > 0:
            print(f"  📈 {stem}: fidelity {s['supported']}/{s['total_fields']} "
                  f"({s['supported'] / s['total_fields'] * 100:.0f}%) | "
                  f"corrections {s['total_corrections']}")
    elif status == "skipped":
        print(f"  ⏭️  {stem}: skipped")


def process_one_paper(md_path: Path, stem: str, tracker: TokenTracker):
    """处理单篇论文：提取 + 验证（线程安全）。[PR 改动] 使用 GENE_ARRAY_KEY_NAMES 替代硬编码

    流程：extract_paper() → verify_paper() → 返回结果 dict
    在 ThreadPoolExecutor 中并行调用，每篇论文独立处理。
    """
    try:
        extraction, gene_dict = extract_paper(md_path, tracker)

        if extraction is None:
            print(f"  ❌ Extraction failed, skip verify: {stem}")
            return {"status": "failed", "report": None}

        total_genes = sum(
            len(extraction.get(k, []))
            for k in GENE_ARRAY_KEY_NAMES
        )
        print(f"  📊 Extracted {total_genes} genes, dict: {gene_dict}")

        report = verify_paper(md_path, extraction, stem, tracker)
        if report is None:
            return {"status": "failed", "report": None}
        if report.get("status") == "skipped":
            return report
        return {"status": "processed", "report": report}

    except Exception as e:
        print(f"  ❌ Error processing {stem}: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "failed", "report": None}


def print_verify_summary(all_reports: list):
    """打印所有论文的验证汇总统计。

    统计总字段数、SUPPORTED/UNSUPPORTED/UNCERTAIN 数量、修正数、整体准确率。
    """
    if not all_reports:
        return

    print(f"\n{'=' * 60}")
    print(f"📊 Verification Summary")
    print(f"{'=' * 60}")

    total_files = len(all_reports)
    total_fields = sum(r["summary"]["total_fields"] for r in all_reports)
    total_supported = sum(r["summary"]["supported"] for r in all_reports)
    total_unsupported = sum(r["summary"]["unsupported"] for r in all_reports)
    total_uncertain = sum(r["summary"]["uncertain"] for r in all_reports)
    total_corrections = sum(r["summary"]["total_corrections"] for r in all_reports)

    print(f"  Files verified: {total_files}")
    print(f"  Fields checked: {total_fields}")
    print(f"  ✅ SUPPORTED:   {total_supported}")
    print(f"  ❓ UNCERTAIN:   {total_uncertain}")
    print(f"  ❌ UNSUPPORTED: {total_unsupported}")
    print(f"  🔧 Corrections: {total_corrections}")

    if total_fields > 0:
        accuracy = total_supported / total_fields * 100
        print(f"  📈 Fidelity:    {accuracy:.1f}%")


def save_token_report(
    tracker: TokenTracker,
    prefix: str = "pipeline",
    output_dir: Optional[Path] = None,
) -> Optional[str]:
    """Persist the current token tracker and return the saved report path."""
    if not tracker or not tracker.calls:
        return None

    report_dir = Path(output_dir or TOKEN_USAGE_DIR)
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"{prefix}-{timestamp}.json"
    tracker.save_report(str(report_path))
    return str(report_path)


def run_pipeline_batch(
    files: list[str],
    *,
    input_dir: Optional[Path] = None,
    workers: int = MAX_WORKERS,
    tracker: Optional[TokenTracker] = None,
    stop_requested: Optional[Callable[[], bool]] = None,
    on_paper_start: Optional[Callable[[str, int, int, bool], None]] = None,
    on_paper_done: Optional[Callable[[str, dict, int, int, bool], None]] = None,
) -> dict:
    """Run a batch of papers using the shared extractor pipeline orchestration.

    This is the reusable core for both CLI and `/admin`:
    - CLI uses it for normal batch processing + terminal output
    - admin uses it for SSE progress, stop checks, and token tracking

    The web layer stays responsible for auth/UI/index rebuild; extractor owns
    the actual paper-processing loop and token-report inputs.
    """
    input_dir = Path(input_dir or INPUT_DIR)
    tracker = tracker or TokenTracker(model=MODEL)
    total = len(files)
    all_reports = []
    failed_files = []
    skipped_files = []
    stopped = False
    submitted = 0
    done_count = 0
    is_parallel = total > 1 and workers > 1

    if not is_parallel:
        for i, filename in enumerate(files):
            if stop_requested and stop_requested():
                stopped = True
                break

            if on_paper_start:
                on_paper_start(filename, i, total, False)

            md_path = input_dir / filename
            stem = Path(filename).stem
            result = process_one_paper(md_path, stem, tracker)
            collect_paper_result(filename, result, all_reports, failed_files, skipped_files)

            done_count = i + 1
            if on_paper_done:
                on_paper_done(filename, result, done_count, total, False)
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            future_to_file = {}

            for filename in files:
                if stop_requested and stop_requested():
                    stopped = True
                    break

                if on_paper_start:
                    on_paper_start(filename, submitted, total, True)

                md_path = input_dir / filename
                stem = Path(filename).stem
                future = pool.submit(process_one_paper, md_path, stem, tracker)
                future_to_file[future] = filename
                submitted += 1

            for future in as_completed(future_to_file):
                filename = future_to_file[future]
                try:
                    result = future.result()
                except Exception as e:
                    print(f"  ❌ {filename}: {e}")
                    result = {"status": "failed", "report": None}

                collect_paper_result(filename, result, all_reports, failed_files, skipped_files)

                done_count += 1
                if on_paper_done:
                    on_paper_done(filename, result, done_count, total, True)

    return {
        "tracker": tracker,
        "all_reports": all_reports,
        "failed_files": failed_files,
        "skipped_files": skipped_files,
        "stopped": stopped,
        "submitted": submitted if is_parallel else done_count,
        "done": done_count,
        "total": total,
    }


def main():
    """Pipeline 主函数：解析参数 → 发现文件 → 顺序/并行处理 → 汇总输出。[PR 改动] 拆出 collect_paper_result/_print_paper_result"""
    parser = argparse.ArgumentParser(description="NutriMaster Extraction Pipeline")
    parser.add_argument("--test", type=str, default=None,
                        help="Test mode: file index (1-based) or filename pattern")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS,
                        help=f"Parallel workers (default: {MAX_WORKERS})")
    args = parser.parse_args()

    ensure_dirs()

    # ── Pipeline mode ─────────────────────────────────────────────────────────
    print("═" * 60)
    print("🚀 NutriMaster Pipeline")
    print(f"   Model:     {MODEL}")
    print(f"   Input:     {INPUT_DIR}")
    print(f"   Workers:   {args.workers}")
    print("═" * 60)

    input_dir = Path(INPUT_DIR)
    if not input_dir.exists():
        print(f"❌ Input dir does not exist: {input_dir}")
        return

    files = sorted([f for f in os.listdir(input_dir) if f.endswith(".md")])
    print(f"📂 Found {len(files)} files")

    # Test mode
    if args.test is not None:
        files = resolve_test_files(files, args.test)
        if not files:
            return
    elif os.getenv("TEST_MODE") == "1":
        test_index = os.getenv("TEST_INDEX", "1")
        files = resolve_test_files(files, test_index)
        if not files:
            return

    workers = args.workers
    is_parallel = len(files) > 1 and workers > 1
    tracker = TokenTracker(model=MODEL)

    def _on_paper_start(filename: str, index: int, total: int, parallel: bool):
        # CLI 只在顺序模式下打印单篇头部，避免并行日志互相打乱。
        if not parallel:
            print(f"\n{'━' * 60}")
            print(f"📄 [{index + 1}/{total}] {filename}")
            print(f"{'━' * 60}")

    def _on_paper_done(filename: str, result: dict, done: int, total: int, parallel: bool):
        stem = Path(filename).stem
        _print_paper_result(stem, result)

    if is_parallel:
        print(f"\n🔄 Processing {len(files)} papers with {workers} workers...\n")

    run_result = run_pipeline_batch(
        files,
        input_dir=input_dir,
        workers=workers,
        tracker=tracker,
        on_paper_start=_on_paper_start,
        on_paper_done=_on_paper_done,
    )
    all_reports = run_result["all_reports"]
    failed_files = run_result["failed_files"]
    skipped_files = run_result["skipped_files"]

    # ── Summary ───────────────────────────────────────────────────────────────
    if all_reports:
        print_verify_summary(all_reports)

    tracker.print_summary()
    save_token_report(tracker, "pipeline")

    if failed_files:
        print(f"\n⚠️  {len(failed_files)} files failed: {failed_files}")
        print(f"   Tip: FORCE_RERUN=1 bash src/nutrimaster/extraction/run.sh pipeline")
    if skipped_files:
        print(f"\n⏭️  {len(skipped_files)} files skipped: {skipped_files}")

    print(f"\n✅ Pipeline done! Processed {len(files)}, verified {len(all_reports)}")


if __name__ == "__main__":
    main()
