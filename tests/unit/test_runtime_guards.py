from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def test_rag_config_has_no_embedded_default_key(monkeypatch):
    monkeypatch.delenv("JINA_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    from shared.settings import Settings

    settings = Settings.from_env(env={}, project_root=ROOT)

    assert settings.jina_api_key == ""


def test_retriever_requires_jina_api_key(monkeypatch):
    monkeypatch.delenv("JINA_API_KEY", raising=False)

    from retrieval.jina_retriever import JinaRetriever
    from shared.settings import Settings

    retriever = JinaRetriever(
        index_path=ROOT / "data" / "index",
        settings=Settings.from_env(env={}, project_root=ROOT),
    )

    with pytest.raises(RuntimeError, match="JINA_API_KEY"):
        retriever.get_query_embedding("PSY1")
