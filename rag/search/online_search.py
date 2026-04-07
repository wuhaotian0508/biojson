"""
联网搜索模块 — PubMed E-utilities API

职责：
  - 自动检测中文查询并用 LLM 翻译为英文 PubMed 检索词
  - 调用 PubMed esearch → efetch 获取文献摘要
  - 将结果统一为标准 dict 格式，供后续 rerank 和 LLM 生成使用

返回的每条结果格式：
  {
    "source_type": "pubmed",
    "title": "文章标题",
    "content": "摘要文本",
    "url": "https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
    "score": 0.0,
    "metadata": {"pmid": "...", "journal": "..."}
  }
"""
import logging
import re
import time
import xml.etree.ElementTree as ET
from typing import List, Dict

import openai
import requests
from openai import OpenAI

from config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    FALLBACK_API_KEY,
    FALLBACK_BASE_URL,
    FALLBACK_MODEL,
    PUBMED_ESEARCH_URL,
    PUBMED_EFETCH_URL,
    PUBMED_MAX_RESULTS,
)

logger = logging.getLogger(__name__)

# ---- 检测文本中是否含有 CJK（中日韩）字符，用于判断是否需要翻译 ----
_HAS_CJK = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')


class OnlineSearcher:
    """PubMed 联网搜索器 — 支持中英文查询"""

    def __init__(self):
        # ---- 主 LLM 客户端（用于中文查询翻译） ----
        self._llm = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

        # ---- Fallback LLM 客户端（主 API 内容过滤报 400 时切换） ----
        # 翻译失败不会阻断搜索（已有 except Exception 兜底返回原文），
        # 但有 fallback 时可以尝试用备用模型完成翻译
        self._fallback_llm = (
            OpenAI(api_key=FALLBACK_API_KEY, base_url=FALLBACK_BASE_URL)
            if FALLBACK_API_KEY else None
        )
        # _fallback_model：fallback 使用的模型名；未配置时退回主模型名
        self._fallback_model = FALLBACK_MODEL or LLM_MODEL

    # ------------------------------------------------------------------
    # 查询翻译（中文 → 英文 PubMed 检索词）
    # ------------------------------------------------------------------
    def _translate_query(self, query: str) -> str:
        """如果查询包含中文，用 LLM 翻译为英文 PubMed 检索词"""
        if not _HAS_CJK.search(query):
            return query
        # messages: 翻译任务的对话消息列表
        messages = [
            {"role": "system", "content": "You are a translator. Convert the user's biomedical query into an English PubMed search query. Output ONLY the English query, nothing else."},
            {"role": "user", "content": query},
        ]
        try:
            resp = self._llm.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=0,
                max_tokens=200,
            )
        except openai.BadRequestError:
            # 主 API 内容过滤：尝试 fallback；fallback 也不可用则退回原文
            if self._fallback_llm:
                try:
                    resp = self._fallback_llm.chat.completions.create(
                        model=self._fallback_model,
                        messages=messages,
                        temperature=0,
                        max_tokens=200,
                    )
                except Exception as e:
                    logger.warning("Fallback translation also failed: %s", e)
                    return query
            else:
                return query
        except Exception as e:
            # 其他异常（网络超时等）：不触发 fallback，直接返回原文继续搜索
            logger.warning("Query translation failed, using original: %s", e)
            return query
        # translated: LLM 返回的英文 PubMed 检索词
        translated = resp.choices[0].message.content.strip()
        logger.info("Query translated: %r -> %r", query, translated)
        return translated

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
                title = "".join(title_el.itertext()).strip() if title_el is not None else ""

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
