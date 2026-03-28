import importlib
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
RAG_DIR = ROOT / "rag"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(RAG_DIR))


def test_rag_config_has_no_embedded_default_key(monkeypatch):
    monkeypatch.delenv("JINA_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    config = importlib.import_module("rag.config")
    config = importlib.reload(config)

    assert config.JINA_API_KEY == ""


def test_retriever_requires_jina_api_key(monkeypatch):
    monkeypatch.delenv("JINA_API_KEY", raising=False)

    config = importlib.import_module("rag.config")
    importlib.reload(config)

    retriever_module = importlib.import_module("rag.retriever")
    retriever_module = importlib.reload(retriever_module)

    with pytest.raises(ValueError, match="JINA_API_KEY"):
        retriever_module.JinaRetriever()
