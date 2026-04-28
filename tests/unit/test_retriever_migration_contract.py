from __future__ import annotations

import importlib
import inspect
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_stack_defaults_use_canonical_jina_retriever():
    import nutrimaster.agent.stack as stack_module

    source = inspect.getsource(stack_module._defaults)

    assert "search.retriever" not in source
    assert "nutrimaster.rag.jina_retriever" in source


def test_legacy_search_retriever_facade_is_removed():
    canonical_retriever = importlib.import_module("nutrimaster.rag.jina_retriever")

    assert hasattr(canonical_retriever, "JinaRetriever")
    assert not (ROOT / "rag" / "search" / "retriever.py").exists()
