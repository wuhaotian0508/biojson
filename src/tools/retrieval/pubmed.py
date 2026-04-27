from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from typing import ClassVar

import httpx

from tools import BaseTool
from tools.retrieval.formatters import render_pubmed

logger = logging.getLogger(__name__)

PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


class PubmedQueryOptimizer:
    def __init__(self, *, api_key: str, base_url: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def __call__(self, user_query: str) -> str:
        if not self.api_key or not self.base_url:
            return user_query
        if len(user_query.split()) <= 8 and any(op in user_query.upper() for op in ["AND", "OR", "NOT"]):
            return user_query
        prompt = f"""将以下生物学查询转换为 PubMed 搜索关键词。

用户查询: {user_query}

要求:
1. 提取 2-5 个核心关键词（基因名、化合物名、物种名、生物学过程）
2. 使用英文
3. 用 AND 连接必需词，OR 连接同义词
4. 总词数不超过 10 个
5. 只返回关键词组合，不要解释

现在处理上面的查询，只返回关键词组合:"""
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 200,
                    },
                )
                response.raise_for_status()
                optimized = response.json()["choices"][0]["message"]["content"].strip()
                return re.sub(r"^```.*?\n|```$", "", optimized, flags=re.MULTILINE).strip()
        except Exception as exc:
            logger.warning("PubMed query optimization failed: %s", exc)
            return user_query


class PubmedSearchTool(BaseTool):
    name = "pubmed_search"
    description = "搜索 PubMed 生物医学文献数据库，返回相关论文的标题、摘要、期刊和链接"
    source_type: ClassVar[str] = "pubmed"

    def __init__(self, *, http_client_factory=None, query_optimizer=None):
        self._http_client_factory = http_client_factory or (lambda: httpx.AsyncClient(timeout=20))
        self._query_optimizer = query_optimizer or (lambda query: query)

    @property
    def schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": (
                    "搜索 PubMed 生物医学文献数据库，返回相关论文的标题、摘要、期刊和链接。"
                    "适合查询基因、蛋白质、疾病、药物等生物医学主题。"
                    "查询词建议使用英文以获得最佳结果。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "PubMed 检索词，例如 'CRISPR gene editing crop yield'",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "最大返回条数，默认 5",
                        },
                    },
                    "required": ["query"],
                },
            },
        }

    async def _optimize(self, query: str) -> str:
        result = self._query_optimizer(query)
        if hasattr(result, "__await__"):
            return await result
        return result

    def _parse_pubmed_xml(self, xml_text: str) -> list[dict]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []
        results = []
        for article in root.iter("PubmedArticle"):
            try:
                medline = article.find("MedlineCitation")
                if medline is None:
                    continue
                pmid_element = medline.find("PMID")
                article_element = medline.find("Article")
                if article_element is None:
                    continue
                title_element = article_element.find("ArticleTitle")
                abstract_element = article_element.find("Abstract")
                abstract_parts = []
                if abstract_element is not None:
                    for text_element in abstract_element.findall("AbstractText"):
                        label = text_element.get("Label", "")
                        text = "".join(text_element.itertext()).strip()
                        abstract_parts.append(f"{label}: {text}" if label else text)
                journal_element = article_element.find("Journal/Title")
                pmid = pmid_element.text if pmid_element is not None else ""
                results.append(
                    {
                        "pmid": pmid,
                        "title": "".join(title_element.itertext()).strip() if title_element is not None else "",
                        "abstract": "\n".join(abstract_parts) or "(no abstract)",
                        "journal": journal_element.text if journal_element is not None else "",
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    }
                )
            except Exception:
                continue
        return results

    async def search_raw(self, query: str, max_results: int = 5, *, optimize: bool = True) -> list[dict]:
        search_query = await self._optimize(query) if optimize else query
        client = self._http_client_factory()
        close = getattr(client, "aclose", None)
        try:
            response = await client.get(
                PUBMED_ESEARCH_URL,
                params={
                    "db": "pubmed",
                    "term": search_query,
                    "retmax": max_results,
                    "retmode": "json",
                    "sort": "relevance",
                },
            )
            response.raise_for_status()
            ids = response.json().get("esearchresult", {}).get("idlist", [])
            if not ids:
                return []
            response = await client.get(
                PUBMED_EFETCH_URL,
                params={
                    "db": "pubmed",
                    "id": ",".join(ids),
                    "retmode": "xml",
                    "rettype": "abstract",
                },
            )
            response.raise_for_status()
        finally:
            if close is not None:
                await close()

        return [
            {
                "source_type": self.source_type,
                "title": article["title"],
                "content": article["abstract"],
                "url": article["url"],
                "score": 0.0,
                "metadata": {
                    "pmid": article["pmid"],
                    "journal": article["journal"],
                },
            }
            for article in self._parse_pubmed_xml(response.text)
        ]

    async def execute(self, query: str, max_results: int = 5, **_) -> str:
        optimized_query = await self._optimize(query)
        articles = await self.search_raw(optimized_query, max_results, optimize=False)
        if not articles:
            return f"未找到与 '{query}' 相关的 PubMed 文献。"
        lines = [f"PubMed 搜索结果（共 {len(articles)} 篇）：\n"]
        for index, article in enumerate(articles, 1):
            lines.extend(render_pubmed(article, index, with_source_label=False))
            lines.append("")
        return "\n".join(lines)


PubMedSearchTool = PubmedSearchTool
