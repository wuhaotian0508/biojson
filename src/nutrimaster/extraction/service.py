from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nutrimaster.extraction.config import INPUT_DIR, MAX_WORKERS, ensure_dirs
from nutrimaster.extraction.config import EXTRACTOR_MODEL
from nutrimaster.extraction.pipeline import (
    resolve_test_files,
    run_pipeline_batch,
    save_token_report,
)
from nutrimaster.extraction.token_tracker import TokenTracker


@dataclass(frozen=True)
class ExtractionRunResult:
    files: list[str]
    processed: int
    failed: list[str]
    skipped: list[str]
    stopped: bool
    token_report: str | None


class ExtractionService:
    """Human-facing markdown-to-corpus extraction boundary for CLI and admin."""

    def __init__(self, *, input_dir: Path | None = None):
        self.input_dir = Path(input_dir or INPUT_DIR)

    def list_inputs(self) -> list[str]:
        if not self.input_dir.exists():
            return []
        return sorted(path.name for path in self.input_dir.glob("*.md"))

    def run(
        self,
        *,
        test: str | None = None,
        workers: int | None = None,
        stop_requested=None,
        on_paper_start=None,
        on_paper_done=None,
        report_prefix: str = "extract",
    ) -> ExtractionRunResult:
        ensure_dirs()
        files = self.list_inputs()
        if test:
            files = resolve_test_files(files, test)
        tracker = TokenTracker(model=EXTRACTOR_MODEL or "unknown")
        result = run_pipeline_batch(
            files,
            input_dir=self.input_dir,
            workers=workers or MAX_WORKERS,
            tracker=tracker,
            stop_requested=stop_requested,
            on_paper_start=on_paper_start,
            on_paper_done=on_paper_done,
        )
        token_report = save_token_report(tracker, report_prefix)
        return ExtractionRunResult(
            files=files,
            processed=len(result.get("all_reports", [])),
            failed=result.get("failed_files", []),
            skipped=result.get("skipped_files", []),
            stopped=bool(result.get("stopped", False)),
            token_report=token_report,
        )
