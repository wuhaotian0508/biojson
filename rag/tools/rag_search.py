"""
RAG 综合搜索工具 — 合并 PubMed / 基因库 / 个人库检索 + Jina 重排

吸收自 pipeline.py 的搜索+重排逻辑，封装为 Agent 可调用的 tool。
Agent 调用此工具获取排序后的检索结果，再自行生成回答。
"""
import asyncio
import logging

logger = logging.getLogger(__name__)


class RAGSearchTool:
    name = "rag_search"
    description = "综合搜索 PubMed 文献、基因数据库和个人知识库，返回重排后的最相关结果"

    def __init__(self, pubmed_tool, retriever, reranker,
                 get_personal_lib=None, get_query_embedding=None):
        """
        参数:
            pubmed_tool:        PubmedSearchTool 实例（复用 search_raw）
            retriever:          JinaRetriever 实例（基因库向量检索）
            reranker:           JinaReranker 实例（跨来源语义重排）
            get_personal_lib:   user_id -> PersonalLibrary 的回调
            get_query_embedding: query -> np.ndarray 的同步回调
        """
        self._pubmed = pubmed_tool
        self._retriever = retriever
        self._reranker = reranker
        self._get_personal_lib = get_personal_lib
        self._get_query_embedding = get_query_embedding

    # 运行时由 app.py 注入当前请求的 user_id
    _current_user_id: str | None = None

    @property
    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询（建议使用英文以获得最佳结果）",
                        },
                        "sources": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["pubmed", "gene_db", "personal_lib"],
                            },
                            "description": (
                                "要搜索的数据源列表。"
                                "pubmed: PubMed 文献；gene_db: 本地基因数据库；"
                                "personal_lib: 用户个人知识库。默认 [\"pubmed\"]"
                            ),
                        },
                        "top_n": {
                            "type": "integer",
                            "description": "返回重排后的结果数量，默认 10",
                        },
                    },
                    "required": ["query"],
                },
            },
        }

    # ------------------------------------------------------------------
    # 各来源搜索（返回统一 dict 格式）
    # ------------------------------------------------------------------

    async def _search_pubmed(self, query: str) -> list[dict]:
        """通过 PubmedSearchTool.search_raw 获取结构化结果"""
        try:
            return await self._pubmed.search_raw(query)
        except Exception as e:
            logger.warning("PubMed 搜索失败: %s", e)
            return []

    async def _search_gene_db(self, query: str, top_k: int = 20) -> list[dict]:
        """通过 JinaRetriever.search 获取基因库结果，转换为统一 dict"""
        try:
            chunks = await asyncio.to_thread(self._retriever.search, query, top_k=top_k)
        except Exception as e:
            logger.warning("基因库检索失败: %s", e)
            return []

        results = []
        for chunk, score in chunks:
            results.append({
                "source_type": "gene_db",
                "title": chunk.paper_title,
                "content": chunk.content,
                "url": f"https://doi.org/{chunk.doi}" if chunk.doi else "",
                "score": score,
                "metadata": {
                    "gene_name": chunk.gene_name,
                    "gene_type": chunk.gene_type,
                    "journal": chunk.journal,
                    "doi": chunk.doi,
                },
            })
        return results

    async def _search_personal_lib(self, query: str, top_k: int = 10) -> list[dict]:
        """通过 PersonalLibrary.search 获取个人库结果"""
        user_id = self._current_user_id
        if not user_id or not self._get_personal_lib or not self._get_query_embedding:
            return []

        try:
            lib = self._get_personal_lib(user_id)
            q_emb = await asyncio.to_thread(self._get_query_embedding, query)
            return await asyncio.to_thread(lib.search, q_emb, top_k=top_k)
        except Exception as e:
            logger.warning("个人知识库检索失败: %s", e)
            return []

    # ------------------------------------------------------------------
    # 主执行方法
    # ------------------------------------------------------------------

    async def execute(self, query: str, sources: list[str] | None = None,
                      top_n: int = 10, **_) -> str:
        """综合搜索 + 重排，返回格式化的可读文本"""
        sources = sources or ["pubmed"]

        # 并行搜索各来源
        tasks = []
        source_names = []
        if "pubmed" in sources:
            tasks.append(self._search_pubmed(query))
            source_names.append("PubMed")
        if "gene_db" in sources:
            tasks.append(self._search_gene_db(query))
            source_names.append("基因数据库")
        if "personal_lib" in sources:
            tasks.append(self._search_personal_lib(query))
            source_names.append("个人知识库")

        if not tasks:
            return "未指定有效的搜索数据源。"

        all_results = await asyncio.gather(*tasks)
        candidates = []
        for result_list in all_results:
            candidates.extend(result_list)

        if not candidates:
            return f"在 {', '.join(source_names)} 中未找到与 '{query}' 相关的结果。"

        # 重排
        if len(candidates) > top_n and self._reranker:
            try:
                ranked = await asyncio.to_thread(
                    self._reranker.rerank, query, candidates, top_n,
                )
            except Exception as e:
                logger.warning("重排失败，使用原始顺序: %s", e)
                ranked = candidates[:top_n]
        else:
            ranked = candidates[:top_n]

        return self._format_results(ranked, source_names)

    # ------------------------------------------------------------------
    # 格式化输出
    # ------------------------------------------------------------------

    @staticmethod
    def _format_results(ranked: list[dict], source_names: list[str]) -> str:
        """将重排后的结果格式化为 Agent 可读文本"""
        lines = [f"综合搜索结果（来源: {', '.join(source_names)}，共 {len(ranked)} 条）：\n"]

        for i, item in enumerate(ranked, 1):
            src = item.get("source_type", "unknown")
            meta = item.get("metadata", {})
            title = item.get("title", "")
            score = item.get("score", 0.0)

            if src == "pubmed":
                lines.append(f"[{i}] {title}")
                lines.append(f"    来源: PubMed")
                lines.append(f"    期刊: {meta.get('journal', '')}")
                lines.append(f"    PMID: {meta.get('pmid', '')}")
                lines.append(f"    链接: {item.get('url', '')}")
            elif src == "gene_db":
                lines.append(f"[{i}] {title}")
                lines.append(f"    来源: 基因数据库")
                lines.append(f"    基因: {meta.get('gene_name', '')}")
                lines.append(f"    类型: {meta.get('gene_type', '')}")
                lines.append(f"    期刊: {meta.get('journal', '')}")
                if meta.get("doi"):
                    lines.append(f"    DOI: {meta['doi']}")
            elif src == "personal":
                filename = meta.get("filename", "")
                page = meta.get("page", "")
                lines.append(f"[{i}] {filename} (p.{page})")
                lines.append(f"    来源: 个人知识库")
            else:
                lines.append(f"[{i}] {title}")
                lines.append(f"    来源: {src}")

            lines.append(f"    相关性: {score:.4f}")

            content = item.get("content", "")
            if len(content) > 500:
                content = content[:500] + "..."
            lines.append(f"    内容: {content}")
            lines.append("")

        return "\n".join(lines)
