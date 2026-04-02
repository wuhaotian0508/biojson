"""联网搜索模块 - PubMed API"""
import logging
import re
import time
import xml.etree.ElementTree as ET
from typing import List, Dict

import requests
from openai import OpenAI

from config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    PUBMED_ESEARCH_URL,
    PUBMED_EFETCH_URL,
    PUBMED_MAX_RESULTS,
)

logger = logging.getLogger(__name__)

_HAS_CJK = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')


class OnlineSearcher:
    """PubMed 联网搜索"""

    def __init__(self):
        self._llm = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

    # ------------------------------------------------------------------
    # 查询翻译（中文 → 英文 PubMed 检索词）
    # ------------------------------------------------------------------
    def _translate_query(self, query: str) -> str:
        """如果查询包含中文，用 LLM 翻译为英文 PubMed 检索词"""
        if not _HAS_CJK.search(query):
            return query
        try:
            resp = self._llm.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a translator. Convert the user's biomedical query into an English PubMed search query. Output ONLY the English query, nothing else."},
                    {"role": "user", "content": query},
                ],
                temperature=0,
                max_tokens=200,
            )
            translated = resp.choices[0].message.content.strip()
            logger.info("Query translated: %r -> %r", query, translated)
            return translated
        except Exception as e:
            logger.warning("Query translation failed, using original: %s", e)
            return query

    # ------------------------------------------------------------------
    # PubMed
    # ------------------------------------------------------------------
    def search_pubmed(self, query: str, max_results: int = PUBMED_MAX_RESULTS,
                      max_retries: int = 3) -> List[Dict]:
        """通过 PubMed E-utilities 搜索文献摘要（带重试）"""
        for attempt in range(1, max_retries + 1):
            try:
                # 1. esearch: 获取 PMID 列表
                params = {
                    "db": "pubmed",
                    "term": query,
                    "retmax": max_results,
                    "retmode": "json",
                    "sort": "relevance",
                }
                resp = requests.get(PUBMED_ESEARCH_URL, params=params, timeout=15)
                resp.raise_for_status()
                id_list = resp.json().get("esearchresult", {}).get("idlist", [])
                if not id_list:
                    return []

                # 2. efetch: 获取摘要详情
                params = {
                    "db": "pubmed",
                    "id": ",".join(id_list),
                    "retmode": "xml",
                    "rettype": "abstract",
                }
                resp = requests.get(PUBMED_EFETCH_URL, params=params, timeout=20)
                resp.raise_for_status()

                return self._parse_pubmed_xml(resp.text)

            except Exception as e:
                logger.warning("PubMed search attempt %d/%d failed: %s", attempt, max_retries, e)
                if attempt < max_retries:
                    time.sleep(1 * attempt)
        return []

    def _parse_pubmed_xml(self, xml_text: str) -> List[Dict]:
        """解析 PubMed efetch XML 返回的文献信息"""
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
                title = title_el.text or "" if title_el is not None else ""

                # 摘要可能有多段
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
                    "source_type": "pubmed",
                    "title": title,
                    "content": abstract or title,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "score": 0.0,
                    "metadata": {"pmid": pmid, "journal": journal},
                })
            except Exception:
                continue

        return results

    # ------------------------------------------------------------------
    # 聚合搜索
    # ------------------------------------------------------------------
    def search_all(self, query: str) -> List[Dict]:
        """执行 PubMed 搜索（自动翻译中文查询）"""
        en_query = self._translate_query(query)
        return self.search_pubmed(en_query)
