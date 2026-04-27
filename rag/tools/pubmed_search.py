"""
PubMed 文献搜索工具 — 通过 NCBI E-utilities API 搜索生物医学文献

功能：
  1. 查询优化：用 LLM 将自然语言查询转换为 PubMed 布尔检索式
  2. 两阶段检索：esearch 获取 PMID 列表 → efetch 批量获取文献详情
  3. 结构化输出：返回标题、摘要、期刊、PMID、链接等字段

工作流程：
  用户查询 → LLM 优化为关键词 → esearch API → PMID 列表 → efetch API → XML 解析 → 结构化 dict

注意：
  - 不做 embedding，直接返回原始结果（由 rag_search 的 Reranker 统一重排）
  - 查询优化可选（未配置 LLM 时使用原始查询）
"""
import xml.etree.ElementTree as ET
import re
import json
import logging
from typing import ClassVar, Optional

import httpx

from tools.base import BaseTool

logger = logging.getLogger(__name__)

# NCBI E-utilities API 端点
PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"  # 搜索 PMID
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"    # 获取文献详情

# LLM API 配置（用于查询优化，可选）
_LLM_API_KEY: Optional[str] = None
_LLM_BASE_URL: Optional[str] = None
_LLM_MODEL: Optional[str] = None


def configure_query_optimizer(api_key: str, base_url: str, model: str = "gpt-4o-mini"):
    """
    配置查询优化器的 LLM（在应用启动时调用一次）

    Args:
        api_key: LLM API 密钥
        base_url: LLM API 基础 URL
        model: 模型名称（推荐用小模型，查询优化不需要强推理能力）
    """
    global _LLM_API_KEY, _LLM_BASE_URL, _LLM_MODEL
    _LLM_API_KEY = api_key
    _LLM_BASE_URL = base_url
    _LLM_MODEL = model


async def _optimize_pubmed_query(user_query: str) -> str:
    """
    用 LLM 将自然语言查询转换为 PubMed 优化的布尔检索式

    策略：
      1. 提取 2-5 个核心关键词（基因名、化合物名、物种名、生物学过程）
      2. 使用 AND 连接必需词，OR 连接同义词
      3. 总词数不超过 10 个（PubMed 是关键词匹配，不是语义搜索，长查询效果差）

    Args:
        user_query: 用户的自然语言查询（中文或英文）

    Returns:
        优化后的 PubMed 检索式（英文关键词 + 布尔运算符）

    示例：
        输入: "番茄中α-番茄碱的生物合成途径"
        输出: "(tomatine OR alpha-tomatine) AND tomato AND biosynthesis"
    """
    if not _LLM_API_KEY or not _LLM_BASE_URL:
        logger.warning("查询优化器未配置，使用原始查询")
        return user_query

    # 如果查询已经很短且包含布尔运算符，直接返回（避免重复优化）
    if len(user_query.split()) <= 8 and any(op in user_query.upper() for op in ["AND", "OR", "NOT"]):
        return user_query

    # 构建优化提示词（包含示例，few-shot learning）
    prompt = f"""将以下生物学查询转换为 PubMed 搜索关键词。

用户查询: {user_query}

要求:
1. 提取 2-5 个核心关键词（基因名、化合物名、物种名、生物学过程）
2. 使用英文
3. 用 AND 连接必需词，OR 连接同义词
4. 总词数不超过 10 个
5. 只返回关键词组合，不要解释

示例:
输入: 番茄中α-番茄碱的生物合成途径
输出: (tomatine OR alpha-tomatine) AND tomato AND biosynthesis

输入: CRISPR编辑提高水稻铁含量
输出: CRISPR AND rice AND (iron OR Fe) AND biofortification

输入: 茄科植物中25S和25R构型生物碱的生物学功能差异
输出: Solanaceae AND steroidal AND (25S OR 25R) AND biological activity

现在处理上面的查询，只返回关键词组合:"""

    try:
        # 调用 LLM API（使用小模型，查询优化不需要强推理能力）
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.post(
                f"{_LLM_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {_LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": _LLM_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,  # 低温度保证输出稳定
                    "max_tokens": 200,
                },
            )
            resp.raise_for_status()
            optimized = resp.json()["choices"][0]["message"]["content"].strip()

            # 清理可能的 markdown 代码块（有些模型会用 ```text ... ``` 包裹）
            optimized = re.sub(r'^```.*?\n|```$', '', optimized, flags=re.MULTILINE).strip()

            logger.info(f"查询优化: '{user_query}' → '{optimized}'")
            return optimized

    except Exception as e:
        # 优化失败不影响主流程，降级使用原始查询
        logger.warning(f"查询优化失败，使用原始查询: {e}")
        return user_query


class PubmedSearchTool(BaseTool):
    """
    PubMed 文献搜索工具

    功能：
      - 搜索 NCBI PubMed 数据库（3500万+ 生物医学文献）
      - 自动查询优化（LLM 将自然语言转为布尔检索式）
      - 返回标题、摘要、期刊、PMID、链接

    使用场景：
      - Agent 单独调用：查询最新文献、验证假设
      - rag_search 调用：作为多来源检索的一路（与 gene_db、personal_lib 并行）

    注意：
      - 不做 embedding，直接返回原始结果
      - 由 rag_search 的 Jina Reranker 统一重排
    """
    name = "pubmed_search"
    description = "搜索 PubMed 生物医学文献数据库，返回相关论文的标题、摘要、期刊和链接"
    source_type: ClassVar[str] = "pubmed"  # 用于 rag_search 识别来源类型

    @property
    def schema(self):
        """返回 LLM function calling schema（Agent 用于理解工具功能和参数）"""
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
        """工具执行超时时间（秒）"""
        return 60

    def _parse_pubmed_xml(self, xml_text: str) -> list[dict]:
        """
        解析 PubMed efetch 返回的 XML，提取文献元数据

        Args:
            xml_text: efetch API 返回的 XML 字符串

        Returns:
            文献列表，每个元素包含 pmid、title、abstract、journal、url

        XML 结构示例：
            <PubmedArticleSet>
              <PubmedArticle>
                <MedlineCitation>
                  <PMID>12345678</PMID>
                  <Article>
                    <ArticleTitle>Title here</ArticleTitle>
                    <Abstract>
                      <AbstractText Label="BACKGROUND">...</AbstractText>
                      <AbstractText Label="METHODS">...</AbstractText>
                    </Abstract>
                    <Journal><Title>Journal Name</Title></Journal>
                  </Article>
                </MedlineCitation>
              </PubmedArticle>
            </PubmedArticleSet>
        """
        results = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return results

        # 遍历每篇文献
        for article in root.iter("PubmedArticle"):
            try:
                # 提取 PMID
                medline = article.find("MedlineCitation")
                pmid_el = medline.find("PMID")
                pmid = pmid_el.text if pmid_el is not None else ""

                # 提取标题
                art = medline.find("Article")
                title_el = art.find("ArticleTitle")
                title = "".join(title_el.itertext()).strip() if title_el is not None else ""

                # 提取摘要（可能有多段，如 BACKGROUND / METHODS / RESULTS）
                abstract_parts = []
                abstract_el = art.find("Abstract")
                if abstract_el is not None:
                    for ab_text in abstract_el.findall("AbstractText"):
                        label = ab_text.get("Label", "")  # 段落标签（可选）
                        text = "".join(ab_text.itertext()).strip()
                        if label:
                            abstract_parts.append(f"{label}: {text}")
                        else:
                            abstract_parts.append(text)
                abstract = "\n".join(abstract_parts)

                # 提取期刊名
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
                # 单篇文献解析失败不影响其他文献
                continue

        return results

    async def search_raw(self, query: str, max_results: int = 5) -> list[dict]:
        """
        调用 PubMed API 搜索文献，返回结构化 dict 列表

        这是底层方法，供 rag_search 等工具复用（不做格式化，只返回原始数据）

        Args:
            query: 搜索查询（会自动优化）
            max_results: 最大返回条数

        Returns:
            文献列表，每个元素包含：
              - title: 标题
              - content: 摘要文本
              - url: PubMed 链接
              - score: 固定为 1.0（PubMed API 不返回相关性分数）
              - metadata: {pmid, journal}

        工作流程：
            1. LLM 优化查询（可选）
            2. esearch API 获取 PMID 列表
            3. efetch API 批量获取文献详情
            4. 解析 XML 返回结构化数据
        """
        # 第一步：LLM 优化查询
        optimized_query = await _optimize_pubmed_query(query)
        if optimized_query != query:
            logger.info(f"PubMed 查询优化: '{query[:80]}...' → '{optimized_query}'")

        async with httpx.AsyncClient(timeout=20) as client:
            # 第二步：esearch — 用关键词搜索，获取 PMID 列表
            resp = await client.get(PUBMED_ESEARCH_URL, params={
                "db": "pubmed",
                "term": optimized_query,  # 搜索词
                "retmax": max_results,    # 最大返回数
                "retmode": "json",        # 返回 JSON 格式
                "sort": "relevance",      # 按相关性排序
            })
            resp.raise_for_status()
            id_list = resp.json().get("esearchresult", {}).get("idlist", [])

            if not id_list:
                return []

            # 第三步：efetch — 用 PMID 列表批量获取文献详情（XML 格式含完整摘要）
            resp = await client.get(PUBMED_EFETCH_URL, params={
                "db": "pubmed",
                "id": ",".join(id_list),  # 逗号分隔的 PMID 列表
                "retmode": "xml",         # XML 格式（包含完整元数据）
                "rettype": "abstract",    # 摘要级别
            })
            resp.raise_for_status()

        # 第四步：解析 XML → 结构化 dict
        articles = self._parse_pubmed_xml(resp.text)
        # 转换为统一的 SearchSource 输出格式（供 rag_search 重排使用）
        results = []
        for a in articles:
            results.append({
                "source_type": "pubmed",       # 来源标识（rag_search 用于分类）
                "title": a["title"],           # 论文标题
                "content": a["abstract"],      # 摘要文本（Reranker 用于计算相关性）
                "url": a["url"],               # PubMed 链接
                "score": 0.0,                  # 初始分数（由 Reranker 重新计算）
                "metadata": {
                    "pmid": a["pmid"],         # PubMed ID
                    "journal": a["journal"],   # 期刊名
                },
            })
        return results

    async def execute(self, query: str, max_results: int = 5, **_) -> str:
        """
        Agent 直接调用的入口 — 返回格式化的可读文本

        与 search_raw 的区别：
          - search_raw：返回 list[dict]，供 rag_search 聚合使用
          - execute：返回格式化的字符串，直接注入 Agent 消息

        Args:
            query: 搜索查询
            max_results: 最大返回条数

        Returns:
            格式化的文献列表文本，包含编号、标题、期刊、PMID、链接、摘要
        """
        from tools._formatters import render_pubmed
        from core.hooks import log_query_optimization

        # 优化查询
        optimized_query = await _optimize_pubmed_query(query)

        # 记录优化结果（如果查询被修改）
        if optimized_query != query:
            logger.info(f"PubMed 查询优化: '{query[:80]}...' → '{optimized_query}'")
            # 记录到工具调用日志
            log_query_optimization(
                tool_name="pubmed_search",
                original_query=query,
                optimized_query=optimized_query,
            )

        articles = await self.search_raw(optimized_query, max_results)

        if not articles:
            return f"未找到与 '{query}' 相关的 PubMed 文献。"

        lines = [f"PubMed 搜索结果（共 {len(articles)} 篇）：\n"]
        for i, a in enumerate(articles, 1):
            lines.extend(render_pubmed(a, i, with_source_label=False))
            lines.append("")

        return "\n".join(lines)


# 别名：兼容 app.py 中 PubMedSearchTool 大小写导入
PubMedSearchTool = PubmedSearchTool


if __name__ == "__main__":
    import asyncio
    tool = PubmedSearchTool()
    result = asyncio.run(tool.execute("vitamin C biosynthesis rice"))
    print(result)
