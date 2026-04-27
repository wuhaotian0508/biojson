from __future__ import annotations

from types import SimpleNamespace


def test_gene_db_search_tool_uses_retrieval_service_and_formats_results():
    import asyncio
    import inspect

    from retrieval.tools import GeneDBSearchTool
    import retrieval.tools.gene_db as gene_db_module

    assert "rag.tools" not in inspect.getsource(gene_db_module)

    chunk = SimpleNamespace(
        paper_title="Tomato carotenoid paper",
        content="PSY1 controls carotenoid biosynthesis in tomato fruit.",
        doi="10.example/psy1",
        gene_name="PSY1",
        gene_type="Pathway_Genes",
        journal="Plant Cell",
    )

    class FakeRetrievalService:
        def search_gene_chunks(self, query, *, top_k, use_hybrid, rerank, rerank_top_n):
            assert query == "lycopene"
            assert top_k == 2
            assert use_hybrid is True
            assert rerank is True
            assert rerank_top_n == 50
            return [(chunk, 0.9)]

    tool = GeneDBSearchTool(retrieval_service=FakeRetrievalService())

    raw = asyncio.run(tool.search_raw("lycopene", top_k=2))
    assert raw == [
        {
            "source_type": "gene_db",
            "title": "Tomato carotenoid paper",
            "content": "PSY1 controls carotenoid biosynthesis in tomato fruit.",
            "url": "https://doi.org/10.example/psy1",
            "score": 0.9,
            "metadata": {
                "gene_name": "PSY1",
                "gene_type": "Pathway_Genes",
                "journal": "Plant Cell",
                "doi": "10.example/psy1",
            },
        }
    ]

    rendered = asyncio.run(tool.execute("lycopene", top_k=2))
    assert "基因数据库检索结果" in rendered
    assert "PSY1" in rendered
