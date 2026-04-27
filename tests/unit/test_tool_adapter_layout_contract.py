from __future__ import annotations

import inspect


def test_retrieval_tool_adapters_live_under_neutral_tools_namespace():
    from tools.retrieval import GeneDBSearchTool, PubmedSearchTool, RAGSearchTool
    import retrieval.tools.pubmed as legacy_pubmed_module

    assert PubmedSearchTool.__module__ == "tools.retrieval.pubmed"
    assert GeneDBSearchTool.__module__ == "tools.retrieval.gene_db"
    assert RAGSearchTool.__module__ == "tools.retrieval.rag_search"
    assert "tools.retrieval.pubmed" in inspect.getsource(legacy_pubmed_module)
