from __future__ import annotations

def test_retrieval_tool_adapters_live_under_neutral_tools_namespace():
    from nutrimaster.agent.tools.retrieval import GeneDBSearchTool, PubmedSearchTool, RAGSearchTool

    assert PubmedSearchTool.__module__ == "nutrimaster.agent.tools.retrieval.pubmed"
    assert GeneDBSearchTool.__module__ == "nutrimaster.agent.tools.retrieval.gene_db"
    assert RAGSearchTool.__module__ == "nutrimaster.agent.tools.retrieval.rag_search"
