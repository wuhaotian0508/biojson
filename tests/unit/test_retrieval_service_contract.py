from __future__ import annotations


def test_retrieval_service_delegates_index_build_and_exposes_chunk_count():
    from nutrimaster.rag.gene_index import RetrievalService

    class FakeRetriever:
        def __init__(self):
            self.chunks = ["a", "b"]
            self.calls = []

        def build_index(self, *, force=False, incremental=True):
            self.calls.append((force, incremental))

    retriever = FakeRetriever()
    service = RetrievalService(retriever=retriever)

    service.build_index(force=True, incremental=False)

    assert service.total_chunks == 2
    assert retriever.calls == [(True, False)]


def test_retrieval_service_uses_hybrid_search_by_default():
    from nutrimaster.rag.gene_index import RetrievalService

    class FakeRetriever:
        chunks = ["a"]

        async def hybrid_search(self, query, top_k, rerank, rerank_top_n):
            return [(query, top_k, rerank, rerank_top_n)]

    service = RetrievalService(retriever=FakeRetriever())

    result = service.search_gene_chunks("lycopene", top_k=5)

    assert result == [("lycopene", 5, True, 50)]


def test_retrieval_service_can_fallback_to_dense_search():
    from nutrimaster.rag.gene_index import RetrievalService

    class FakeRetriever:
        chunks = ["a"]

        def search(self, query, top_k):
            return [(query, top_k)]

    service = RetrievalService(retriever=FakeRetriever())

    result = service.search_gene_chunks("PSY1", top_k=3, use_hybrid=False)

    assert result == [("PSY1", 3)]
