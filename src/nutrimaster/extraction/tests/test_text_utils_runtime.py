from nutrimaster.extraction import text_utils


def test_preprocess_md_stays_local(monkeypatch):
    calls = []

    def fake_extract(content):
        calls.append(content)
        return "filtered"

    monkeypatch.setattr(text_utils, "extract_relevant_sections", fake_extract)

    result = text_utils.preprocess_md("line\n\n\nline")

    assert result == "line\n\nline"
    assert calls == []


def test_preprocess_md_for_llm_applies_section_filter(monkeypatch):
    calls = []

    def fake_extract(content, tracker=None):
        calls.append(content)
        return "filtered"

    monkeypatch.setattr(text_utils, "extract_relevant_sections", fake_extract)

    result = text_utils.preprocess_md_for_llm("line")

    assert result == "filtered"
    assert calls == ["line"]
