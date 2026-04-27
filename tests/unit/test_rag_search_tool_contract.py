from __future__ import annotations


class FakeSource:
    def __init__(self, source_type: str, results: list[dict]):
        self.source_type = source_type
        self.results = results
        self.calls = []

    async def search_raw(self, **kwargs):
        self.calls.append(kwargs)
        return self.results


def test_rag_search_tool_aggregates_sources_and_reranks():
    import asyncio
    import inspect

    from retrieval.tools.rag_search import RAGSearchTool
    import retrieval.tools.rag_search as rag_search_module

    assert "rag.tools" not in inspect.getsource(rag_search_module)

    pubmed = FakeSource(
        "pubmed",
        [
            {
                "source_type": "pubmed",
                "title": "PubMed paper",
                "content": "abstract",
                "url": "https://pubmed.example",
                "score": 0.2,
                "metadata": {"journal": "J", "pmid": "1"},
            }
        ],
    )
    gene_db = FakeSource(
        "gene_db",
        [
            {
                "source_type": "gene_db",
                "title": "Gene paper",
                "content": "gene chunk",
                "url": "",
                "score": 0.9,
                "metadata": {"gene_name": "PSY1", "gene_type": "Pathway_Genes", "journal": "Plant", "doi": ""},
            }
        ],
    )

    class FakeReranker:
        def rerank(self, query, documents, top_n):
            return sorted(documents, key=lambda item: item["score"], reverse=True)[:top_n]

    tool = RAGSearchTool(
        sources={"pubmed": pubmed, "gene_db": gene_db},
        reranker=FakeReranker(),
    )

    rendered = asyncio.run(tool.execute("lycopene", top_n=1))

    assert "综合搜索结果" in rendered
    assert "Gene paper" in rendered
    assert "PubMed paper" not in rendered
    assert pubmed.calls == [{"query": "lycopene"}]
    assert gene_db.calls == [{"query": "lycopene"}]


def test_rag_search_tool_passes_user_id_only_to_personal_source():
    import asyncio

    from retrieval.tools.rag_search import RAGSearchTool

    personal = FakeSource("personal", [])
    gene_db = FakeSource("gene_db", [])
    tool = RAGSearchTool(
        sources={"personal_lib": personal, "gene_db": gene_db},
        reranker=None,
    )

    asyncio.run(tool.execute("lycopene", sources=["personal_lib", "gene_db"], user_id="user-1"))

    assert personal.calls == [{"query": "lycopene", "user_id": "user-1"}]
    assert gene_db.calls == [{"query": "lycopene"}]
