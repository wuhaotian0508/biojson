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
    """Collect a paper result into the correct bucket."""
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
    """Filter files for test mode."""
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
    """Print a single paper's result summary (shared by sequential and parallel)."""
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
    """Process a single paper: extract + verify. Thread-safe."""
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
    """Print summary of all verification reports."""
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


def main():
    parser = argparse.ArgumentParser(description="BioJSON Extraction Pipeline")
    parser.add_argument("--test", type=str, default=None,
                        help="Test mode: file index (1-based) or filename pattern")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS,
                        help=f"Parallel workers (default: {MAX_WORKERS})")
    args = parser.parse_args()

    ensure_dirs()

    # ── Pipeline mode ─────────────────────────────────────────────────────────
    print("═" * 60)
    print("🚀 BioJSON Pipeline v4 — Parallel")
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

    tracker = TokenTracker(model=MODEL)
    all_reports = []
    failed_files = []
    skipped_files = []

    # ── Sequential or parallel processing ─────────────────────────────────────
    workers = args.workers
    if len(files) == 1 or workers <= 1:
        # Sequential
        for i, filename in enumerate(files, 1):
            md_path = input_dir / filename
            stem = Path(filename).stem

            print(f"\n{'━' * 60}")
            print(f"📄 [{i}/{len(files)}] {filename}")
            print(f"{'━' * 60}")

            result = process_one_paper(md_path, stem, tracker)
            collect_paper_result(filename, result, all_reports, failed_files, skipped_files)
            _print_paper_result(stem, result)
    else:
        # Parallel
        print(f"\n🔄 Processing {len(files)} papers with {workers} workers...\n")

        with ThreadPoolExecutor(max_workers=workers) as pool:
            future_to_file = {}
            for filename in files:
                md_path = input_dir / filename
                stem = Path(filename).stem
                future = pool.submit(process_one_paper, md_path, stem, tracker)
                future_to_file[future] = filename

            for future in as_completed(future_to_file):
                filename = future_to_file[future]
                try:
                    result = future.result()
                    collect_paper_result(filename, result, all_reports, failed_files, skipped_files)
                    _print_paper_result(Path(filename).stem, result)
                except Exception as e:
                    print(f"  ❌ {filename}: {e}")
                    failed_files.append(filename)

    # ── Summary ───────────────────────────────────────────────────────────────
    if all_reports:
        print_verify_summary(all_reports)

    tracker.print_summary()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    TOKEN_USAGE_DIR.mkdir(parents=True, exist_ok=True)
    tracker.save_report(str(TOKEN_USAGE_DIR / f"pipeline-{timestamp}.json"))

    if failed_files:
        print(f"\n⚠️  {len(failed_files)} files failed: {failed_files}")
        print(f"   Tip: FORCE_RERUN=1 bash extractor/run.sh pipeline")
    if skipped_files:
        print(f"\n⏭️  {len(skipped_files)} files skipped: {skipped_files}")

    print(f"\n✅ Pipeline done! Processed {len(files)}, verified {len(all_reports)}")


if __name__ == "__main__":
    main()
