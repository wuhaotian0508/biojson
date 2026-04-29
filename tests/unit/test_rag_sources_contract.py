from __future__ import annotations


def test_pubmed_source_parses_articles_without_agent_tool_dependency():
    from nutrimaster.rag.service import PubMedSource

    xml = """
    <PubmedArticleSet>
      <PubmedArticle>
        <MedlineCitation>
          <PMID>123</PMID>
          <Article>
            <ArticleTitle>GAME8 regulates steroidal glycoalkaloids</ArticleTitle>
            <Abstract><AbstractText>GAME8 evidence.</AbstractText></Abstract>
            <Journal><Title>Plant Journal</Title></Journal>
          </Article>
        </MedlineCitation>
      </PubmedArticle>
    </PubmedArticleSet>
    """

    articles = PubMedSource._parse_pubmed_xml(xml)

    assert articles == [
        {
            "pmid": "123",
            "title": "GAME8 regulates steroidal glycoalkaloids",
            "abstract": "GAME8 evidence.",
            "journal": "Plant Journal",
            "url": "https://pubmed.ncbi.nlm.nih.gov/123/",
        }
    ]


def test_agent_tools_package_no_longer_contains_retrieval_adapters():
    import nutrimaster.agent.tools as tools

    assert not hasattr(tools, "PubmedSearchTool")
    assert not hasattr(tools, "GeneDBSearchTool")
    assert not hasattr(tools, "PersonalLibSearchTool")


def test_pubmed_source_no_longer_performs_internal_llm_query_optimization():
    import inspect

    from nutrimaster.rag import service

    source = inspect.getsource(service)

    assert "PubMedQueryOptimizer" not in source
    assert "PubMed query optimization failed" not in source
    assert "/chat/completions" not in inspect.getsource(service.PubMedSource)
