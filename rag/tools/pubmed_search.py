"""
PubMed 文献搜索工具 — 通过 E-utilities API 搜索并返回文献摘要
"""
import xml.etree.ElementTree as ET

import httpx

from tools.base import BaseTool

PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


class PubmedSearchTool(BaseTool):
    name = "pubmed_search"
    description = "搜索 PubMed 生物医学文献数据库，返回相关论文的标题、摘要、期刊和链接"

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

    @property
    def timeout(self):
        return 60

    def _parse_pubmed_xml(self, xml_text: str) -> list[dict]:
        """解析 PubMed efetch XML，提取标题、摘要、期刊、PMID"""
        results = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return results

        for article in root.iter("PubmedArticle"):
            try:
                medline = article.find("MedlineCitation")
                pmid_el = medline.find("PMID")
                pmid = pmid_el.text if pmid_el is not None else ""

                art = medline.find("Article")
                title_el = art.find("ArticleTitle")
                title = "".join(title_el.itertext()).strip() if title_el is not None else ""

                # 摘要可能有多段（OBJECTIVES / METHODS / RESULTS …）
                abstract_parts = []
                abstract_el = art.find("Abstract")
                if abstract_el is not None:
                    for ab_text in abstract_el.findall("AbstractText"):
                        label = ab_text.get("Label", "")
                        text = "".join(ab_text.itertext()).strip()
                        if label:
                            abstract_parts.append(f"{label}: {text}")
                        else:
                            abstract_parts.append(text)
                abstract = "\n".join(abstract_parts)

                journal_el = art.find("Journal/Title")
                journal = journal_el.text if journal_el is not None else ""

                results.append({
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract or "(no abstract)",
                    "journal": journal,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                })
            except Exception:
                continue

        return results

    async def search_raw(self, query: str, max_results: int = 5) -> list[dict]:
        """调用 PubMed esearch + efetch，返回结构化 dict 列表（供 rag_search 等复用）"""
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(PUBMED_ESEARCH_URL, params={
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance",
            })
            resp.raise_for_status()
            id_list = resp.json().get("esearchresult", {}).get("idlist", [])

            if not id_list:
                return []

            resp = await client.get(PUBMED_EFETCH_URL, params={
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "xml",
                "rettype": "abstract",
            })
            resp.raise_for_status()

        articles = self._parse_pubmed_xml(resp.text)
        results = []
        for a in articles:
            results.append({
                "source_type": "pubmed",
                "title": a["title"],
                "content": a["abstract"],
                "url": a["url"],
                "score": 0.0,
                "metadata": {
                    "pmid": a["pmid"],
                    "journal": a["journal"],
                },
            })
        return results

    async def execute(self, query: str, max_results: int = 5, **_) -> str:
        """调用 PubMed esearch + efetch，返回格式化的文献列表"""
        articles = await self.search_raw(query, max_results)

        if not articles:
            return f"未找到与 '{query}' 相关的 PubMed 文献。"

        lines = [f"PubMed 搜索结果（共 {len(articles)} 篇）：\n"]
        for i, a in enumerate(articles, 1):
            lines.append(f"[{i}] {a['title']}")
            lines.append(f"    期刊: {a['metadata']['journal']}")
            lines.append(f"    PMID: {a['metadata']['pmid']}")
            lines.append(f"    链接: {a['url']}")
            abstract = a["content"]
            if len(abstract) > 500:
                abstract = abstract[:500] + "..."
            lines.append(f"    摘要: {abstract}")
            lines.append("")

        return "\n".join(lines)


# 别名：兼容 app.py 中 PubMedSearchTool 大小写导入
PubMedSearchTool = PubmedSearchTool


if __name__ == "__main__":
    import asyncio
    tool = PubmedSearchTool()
    result = asyncio.run(tool.execute("vitamin C biosynthesis rice"))
    print(result)
