from __future__ import annotations


class FakeResponse:
    def __init__(self, *, json_data=None, text=""):
        self._json_data = json_data or {}
        self.text = text

    def json(self):
        return self._json_data

    def raise_for_status(self):
        return None


class FakeAsyncClient:
    def __init__(self):
        self.calls = []

    async def get(self, url, params):
        self.calls.append((url, params))
        if "esearch" in url:
            return FakeResponse(json_data={"esearchresult": {"idlist": ["123"]}})
        return FakeResponse(
            text="""
            <PubmedArticleSet>
              <PubmedArticle>
                <MedlineCitation>
                  <PMID>123</PMID>
                  <Article>
                    <ArticleTitle>Tomato lycopene paper</ArticleTitle>
                    <Abstract><AbstractText>Lycopene biosynthesis abstract.</AbstractText></Abstract>
                    <Journal><Title>Plant Journal</Title></Journal>
                  </Article>
                </MedlineCitation>
              </PubmedArticle>
            </PubmedArticleSet>
            """
        )


def test_pubmed_search_tool_uses_injected_optimizer_and_client():
    import asyncio
    import inspect

    from retrieval.tools import PubmedSearchTool
    import retrieval.tools.pubmed as pubmed_module

    assert "rag.tools" not in inspect.getsource(pubmed_module)

    client = FakeAsyncClient()
    optimizer_calls = []

    async def optimizer(query):
        optimizer_calls.append(query)
        return "tomato AND lycopene"

    tool = PubmedSearchTool(http_client_factory=lambda: client, query_optimizer=optimizer)

    raw = asyncio.run(tool.search_raw("番茄红素", max_results=3))

    assert optimizer_calls == ["番茄红素"]
    assert client.calls[0][1]["term"] == "tomato AND lycopene"
    assert client.calls[0][1]["retmax"] == 3
    assert raw[0]["title"] == "Tomato lycopene paper"
    assert raw[0]["metadata"] == {"pmid": "123", "journal": "Plant Journal"}

    rendered = asyncio.run(tool.execute("番茄红素", max_results=3))
    assert "PubMed 搜索结果" in rendered
    assert "Tomato lycopene paper" in rendered
    assert optimizer_calls == ["番茄红素", "番茄红素"]
