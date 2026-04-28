import json
from pathlib import Path

from nutrimaster.extraction import pipeline
from nutrimaster.extraction.token_tracker import TokenTracker


def test_collect_paper_result_treats_skip_as_non_failure():
    all_reports = []
    failed_files = []
    skipped_files = []

    pipeline.collect_paper_result(
        filename="paper.md",
        result={"status": "skipped", "report": None},
        all_reports=all_reports,
        failed_files=failed_files,
        skipped_files=skipped_files,
    )

    assert all_reports == []
    assert failed_files == []
    assert skipped_files == ["paper.md"]


def test_save_token_report_writes_json(tmp_path):
    tracker = TokenTracker(model="test-model")

    class _Usage:
        prompt_tokens = 1
        completion_tokens = 2
        total_tokens = 3

    class _Response:
        usage = _Usage()

    tracker.add(_Response(), stage="extract", file="paper.md")
    report_path = pipeline.save_token_report(tracker, prefix="unit", output_dir=tmp_path)

    assert report_path is not None
    saved = json.loads(Path(report_path).read_text(encoding="utf-8"))
    assert saved["summary"]["total"]["calls"] == 1


def test_run_pipeline_batch_reuses_shared_orchestration(tmp_path, monkeypatch):
    starts = []
    dones = []

    def fake_process(md_path, stem, tracker):
        return {
            "status": "processed",
            "report": {
                "summary": {
                    "total_fields": 2,
                    "supported": 2,
                    "unsupported": 0,
                    "uncertain": 0,
                    "total_corrections": 0,
                }
            },
        }

    monkeypatch.setattr(pipeline, "process_one_paper", fake_process)

    result = pipeline.run_pipeline_batch(
        ["a.md", "b.md"],
        input_dir=tmp_path,
        workers=1,
        tracker=TokenTracker(model="test-model"),
        on_paper_start=lambda filename, index, total, parallel: starts.append((filename, index, total, parallel)),
        on_paper_done=lambda filename, result, done, total, parallel: dones.append((filename, done, total, parallel)),
    )

    assert result["done"] == 2
    assert result["stopped"] is False
    assert len(result["all_reports"]) == 2
    assert starts == [("a.md", 0, 2, False), ("b.md", 1, 2, False)]
    assert dones == [("a.md", 1, 2, False), ("b.md", 2, 2, False)]
