from __future__ import annotations


class FakeSource:
    def __init__(self, source_type, title):
        from nutrimaster.rag.evidence import EvidenceItem

        self.calls = []
        self.item = EvidenceItem(
            source_id="",
            source_type=source_type,
            title=title,
            content=f"{title} content",
            score=1.0,
        )

    async def search(self, query, **kwargs):
        self.calls.append({"query": query, **kwargs})
        return [self.item]


def test_rag_service_always_searches_pubmed_and_gene_db():
    import asyncio

    from nutrimaster.rag.service import RAGSearchContext, RAGSearchService

    pubmed = FakeSource("pubmed", "PubMed SGA paper")
    gene_db = FakeSource("gene_db", "GAME8 curated gene record")
    service = RAGSearchService(pubmed_source=pubmed, gene_db_source=gene_db)

    packet = asyncio.run(
        service.search(
            "GAME8 25R 25S steroidal glycoalkaloids",
            RAGSearchContext(mode="normal", include_personal=False, top_k=5),
        )
    )

    assert pubmed.calls
    assert gene_db.calls
    assert packet.source_counts == {"pubmed": 1, "gene_db": 1}
    assert {item.source_type for item in packet.items} == {"pubmed", "gene_db"}
    assert [item.source_id for item in packet.items] == ["1", "2"]


def test_rag_service_uses_agent_supplied_source_specific_queries():
    import asyncio

    from nutrimaster.rag.service import RAGSearchContext, RAGSearchService

    pubmed = FakeSource("pubmed", "PubMed GLN paper")
    gene_db = FakeSource("gene_db", "Local GS paper")
    service = RAGSearchService(pubmed_source=pubmed, gene_db_source=gene_db)

    asyncio.run(
        service.search(
            "谷氨酰胺合成酶 GS 家族",
            RAGSearchContext(
                pubmed_query="glutamine synthetase AND plant AND GLN1",
                gene_db_query="GS GLN1 GLN2 谷氨酰胺合成酶",
            ),
        )
    )

    assert pubmed.calls[0]["query"] == "glutamine synthetase AND plant AND GLN1"
    assert gene_db.calls[0]["query"] == "GS GLN1 GLN2 谷氨酰胺合成酶"


def test_evidence_packet_exports_stable_citations():
    from nutrimaster.rag.evidence import EvidenceItem, EvidencePacket

    packet = EvidencePacket(
        query="GAME8",
        mode="normal",
        items=[
            EvidenceItem(source_id="1", source_type="gene_db", title="GAME8 paper", content="GAME8 evidence"),
            EvidenceItem(source_id="2", source_type="pubmed", title="PubMed paper", content="PubMed evidence"),
        ],
    )

    text = packet.to_tool_text()

    assert "[1] GAME8 paper" in text
    assert packet.citations[0]["tool_index"] == 1
    assert packet.citations[0]["source_type"] == "gene_db"


def test_evidence_item_drops_invalid_doi_link_values():
    from nutrimaster.rag.evidence import EvidenceItem

    item = EvidenceItem(
        source_id="1",
        source_type="gene_db",
        title="GAME8 paper",
        content="evidence",
        doi="NA",
    )

    assert item.doi == ""
    assert item.url == ""
    assert "DOI:" not in item.to_prompt_block()
    assert item.to_citation()["url"] == ""


def test_source_collector_dedupes_same_paper_across_sources_and_punctuation():
    from nutrimaster.rag.evidence import EvidenceItem, SourceCollector

    items = [
        EvidenceItem(
            source_id="",
            source_type="gene_db",
            title="Enzymatic twists evolved stereo-divergent alkaloids in the Solanaceae family.",
            content="gene db evidence",
            doi="NA",
        ),
        EvidenceItem(
            source_id="",
            source_type="pubmed",
            title="Enzymatic twists evolved stereo-divergent alkaloids in the Solanaceae family",
            content="pubmed evidence",
        ),
    ]

    numbered = SourceCollector().assign(items)

    assert len(numbered) == 1
    assert numbered[0].source_id == "1"


def test_citation_registry_assigns_global_ids_across_packets_and_reuses_duplicates():
    from nutrimaster.rag.evidence import CitationRegistry, EvidenceItem, EvidencePacket

    registry = CitationRegistry()
    first = registry.assign_packet(
        EvidencePacket(
            query="first",
            mode="normal",
            items=[
                EvidenceItem(
                    source_id="1",
                    source_type="gene_db",
                    title="GS1 paper",
                    content="first evidence",
                    doi="10.1000/gs1",
                )
            ],
        )
    )
    second = registry.assign_packet(
        EvidencePacket(
            query="second",
            mode="normal",
            items=[
                EvidenceItem(
                    source_id="1",
                    source_type="pubmed",
                    title="GS1 paper duplicate",
                    content="duplicate evidence",
                    doi="10.1000/gs1",
                ),
                EvidenceItem(
                    source_id="2",
                    source_type="gene_db",
                    title="GS2 paper",
                    content="second evidence",
                    doi="10.1000/gs2",
                ),
            ],
        )
    )

    assert [item.source_id for item in first.items] == ["1"]
    assert [item.source_id for item in second.items] == ["1", "2"]
