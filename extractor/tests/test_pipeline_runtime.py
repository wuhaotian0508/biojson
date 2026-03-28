from extractor import pipeline


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

