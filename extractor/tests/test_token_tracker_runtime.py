import json
import threading
from pathlib import Path

from extractor.token_tracker import TokenTracker


class _Usage:
    prompt_tokens = 1
    completion_tokens = 2
    total_tokens = 3


class _Response:
    usage = _Usage()


def test_save_report_returns_without_deadlock(tmp_path: Path):
    tracker = TokenTracker(model="test-model")
    tracker.add(_Response(), stage="extract", file="paper.md")

    report_path = tmp_path / "token-report.json"
    error = []

    def run_save():
        try:
            tracker.save_report(report_path)
        except Exception as exc:  # pragma: no cover - surfaced via assertion
            error.append(exc)

    worker = threading.Thread(target=run_save, daemon=True)
    worker.start()
    worker.join(timeout=1)

    assert not worker.is_alive(), "save_report() blocked instead of returning"
    assert not error
    saved = json.loads(report_path.read_text(encoding="utf-8"))
    assert saved["summary"]["total"]["calls"] == 1

