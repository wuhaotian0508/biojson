"""
RAG 综合搜索工具 — 跨来源检索聚合 + Jina 重排

功能：
  1. 多来源并行检索：PubMed 文献 + 基因数据库 + 个人知识库
  2. 跨来源语义重排：Jina Reranker 统一计算相关性
  3. 格式化输出：带编号的引用格式（供 Agent 生成回答时引用）

架构设计（Option C - 协议注入）：
  __init__ 接受 `sources: dict[str, SearchSource]`，键为 source_type，值为任
  何实现 SearchSource 协议的对象（见 tools/search_source.py）。

  新增来源的完整步骤：
    1. 实现 SearchSource 协议（`source_type` + `async search_raw`）
    2. 在 tools/_formatters.py 的 RENDERERS 注册一个 renderer
    3. 在调用方（app.py / server.py）的 sources dict 里加一行
  rag_search 本体无需改动。

工作流程：
  用户查询 → 并行调用各 source.search_raw() → 合并候选结果
  → Jina Reranker 跨来源重排 → 格式化输出（带来源标签和编号）

与单独调用 pubmed_search / gene_db_search 的区别：
  - 单独调用：只搜索一个来源，结果未经跨来源重排
  - rag_search：多来源聚合 + 统一重排，结果更全面且相关性更高

注意：
  - 默认已包含 PubMed 搜索，Agent 无需再单独调用 pubmed_search
  - 各来源并行执行（asyncio.gather），单路失败不影响其他路
  - 重排后的结果按相关性降序排列，编号 [1][2][3]... 供 Agent 引用
"""
import asyncio
import logging

from tools.base import BaseTool
from tools.search_source import SearchSource

logger = logging.getLogger(__name__)


# source_key -> 对外展示的中文标签（出现在聚合 header 的「来源:」里）
_SOURCE_LABELS = {
    "pubmed": "PubMed",
    "gene_db": "基因数据库",
    "personal_lib": "个人知识库",
}


class RAGSearchTool(BaseTool):
    name = "rag_search"
    description = "综合搜索 PubMed 文献、基因数据库和个人知识库，返回重排后的最相关结果"

    def __init__(self, sources: dict[str, SearchSource], reranker):
        """
        参数:
            sources:   source_type -> SearchSource 的 dict。
                       例如 {"pubmed": PubmedSearchTool(), "gene_db": ...}。
                       每个 value 必须实现 `async search_raw(query, **kw) -> list[dict]`。
            reranker:  JinaReranker 实例(跨来源语义重排)。
        """
        self._sources = dict(sources)
        self._reranker = reranker

    @property
    def schema(self) -> dict:
        # 动态从 self._sources 取 enum,新增来源时自动反映到 LLM schema 里
        source_keys = list(self._sources.keys())
        default_sources = [k for k in ("pubmed", "gene_db") if k in self._sources] or source_keys

        # 构建来源说明（告知 LLM 默认包含哪些来源）
        sources_desc = f"要搜索的数据源列表。可选: {source_keys}。默认 {default_sources}"
        if "pubmed" in default_sources:
            sources_desc += "。注意：默认已包含 PubMed，无需再单独调用 pubmed_search 工具"

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": (
                    "综合搜索多个数据源（PubMed 文献、基因数据库、个人知识库），"
                    "自动进行跨来源语义重排，返回最相关的结果。"
                    "默认已包含 PubMed 搜索，无需再单独调用 pubmed_search 工具。"
                ),
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
                                "enum": source_keys,
                            },
                            "description": sources_desc,
                        },
                        "top_n": {
                            "type": "integer",
                            "description": "返回重排后的结果数量，默认 10",
                        },
                        "user_id": {
                            "type": "string",
                            "description": "用户 ID（由系统自动注入，不要手动填写）",
                        },
                    },
                    "required": ["query"],
                },
            },
        }

    # ------------------------------------------------------------------
    # 主执行方法
    # ------------------------------------------------------------------

    async def _safe_search(self, src_key: str, **kwargs) -> list[dict]:
        """
        统一包装 tool.search_raw 的异常处理，保证单路失败不影响其他路。

        参数:
            src_key: 来源标识（如 "pubmed", "gene_db", "personal_lib"）
            **kwargs: 传递给 search_raw 的参数（query, user_id 等）

        返回:
            检索结果列表（失败时返回空列表 []）

        异常处理策略：
            - 单个来源失败只记录警告日志，不抛异常
            - 返回空列表，让其他来源继续执行
            - 最终聚合时自动过滤掉空结果
        """
        tool = self._sources.get(src_key)
        if tool is None:
            return []
        try:
            return await tool.search_raw(**kwargs)
        except Exception as e:
            logger.warning("%s 搜索失败: %s", _SOURCE_LABELS.get(src_key, src_key), e)
            return []

    async def execute(self, query: str, sources: list[str] | None = None,
                      top_n: int = 10, user_id: str | None = None, **_) -> str:
        """
        综合搜索 + 重排，返回格式化的可读文本。

        参数:
            query: 搜索查询（中英文均可）
            sources: 要搜索的数据源列表（默认 ["pubmed", "gene_db"]）
            top_n: 返回重排后的结果数量（默认 10）
            user_id: 用户 ID（仅 personal_lib 需要，由系统自动注入）

        返回:
            格式化的检索结果文本，包含：
              - 聚合 header：来源列表 + 总结果数
              - 每条结果：编号 [1][2]... + 来源标签 + 标题 + 元数据 + 内容
              - 参考文献列表：所有结果的标题/文件名（供 Agent 引用）

        工作流程：
            1. 确定搜索来源（默认 pubmed + gene_db）
            2. 并行调用各来源的 search_raw（asyncio.gather）
            3. 合并所有候选结果（可能来自不同来源）
            4. Jina Reranker 跨来源语义重排（如果候选数 > top_n）
            5. 格式化输出（调用 _formatters.RENDERERS）
            6. 统计各来源在 top_n 中的分布（记录日志）

        异常处理：
            - 单个来源失败不影响其他来源（_safe_search 捕获异常）
            - 所有来源都失败时返回提示信息
            - 重排失败时使用原始顺序（降级策略）
        """
        if sources is None:
            # 默认优先用 pubmed + gene_db(若存在),否则用注册的全部 source
            defaults = [k for k in ("pubmed", "gene_db") if k in self._sources]
            sources = defaults or list(self._sources.keys())

        # 并行搜索各来源，保持 caller 提供的顺序（决定聚合 header 中的来源顺序）
        tasks = []
        source_names = []
        for src in sources:
            if src not in self._sources:
                continue
            kwargs: dict = {"query": query}
            if src == "personal_lib":
                kwargs["user_id"] = user_id
            tasks.append(self._safe_search(src, **kwargs))
            source_names.append(_SOURCE_LABELS.get(src, src))

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

        # 统计各来源在重排后的分布
        source_dist = {}
        for item in ranked:
            src = item.get("source_type", "unknown")
            source_dist[src] = source_dist.get(src, 0) + 1
        logger.info(
            "重排后 top_%d 分布: %s (总候选 %d 条)",
            top_n, source_dist, len(candidates)
        )

        return self._format_results(ranked, source_names)

    # ------------------------------------------------------------------
    # 格式化输出
    # ------------------------------------------------------------------

    @staticmethod
    def _format_results(ranked: list[dict], source_names: list[str]) -> str:
        """
        将重排后的结果格式化为 Agent 可读文本。

        参数:
            ranked: 重排后的结果列表（每个元素包含 source_type, title, content, score, metadata）
            source_names: 来源的中文名称列表（用于 header）

        返回:
            格式化的文本，包含：
              - Header: "综合搜索结果（来源: PubMed, 基因数据库，共 10 条）："
              - 每条结果：
                  [1] 标题
                      来源: PubMed
                      期刊: Nature
                      PMID: 12345678
                      链接: https://pubmed.ncbi.nlm.nih.gov/12345678/
                      相关性: 0.8765
                      内容: 摘要文本...
              - 参考文献列表：
                  ==========================================
                  参考文献：
                  [1] 论文标题 1
                  [2] 论文标题 2
                  ...

        格式化规则：
            - 调用 _formatters.RENDERERS[source_type] 渲染每条结果
            - with_source_label=True（聚合视图，显示来源标签）
            - 未知来源使用兜底渲染（保持向后兼容）
            - 参考文献：personal 用 filename，其他用 title
        """
        from tools._formatters import RENDERERS

        lines = [f"综合搜索结果（来源: {', '.join(source_names)}，共 {len(ranked)} 条）：\n"]

        # 收集所有论文标题用于参考文献
        references = []

        for i, item in enumerate(ranked, 1):
            src = item.get("source_type", "unknown")
            renderer = RENDERERS.get(src)

            if renderer is not None:
                lines.extend(renderer(item, i, with_source_label=True))
                # 参考文献名：personal 用 filename，其他用 title
                if src == "personal":
                    references.append(item.get("metadata", {}).get("filename", ""))
                else:
                    references.append(item.get("title", ""))
            else:
                # 未知来源的兜底渲染（保持与历史实现字节一致）
                title = item.get("title", "")
                lines.append(f"[{i}] {title}")
                lines.append(f"    来源: {src}")
                lines.append(f"    相关性: {item.get('score', 0.0):.4f}")
                lines.append(f"    内容: {item.get('content', '')}")
                references.append(title)

            lines.append("")

        # 添加参考文献部分
        if references:
            lines.append("=" * 60)
            lines.append("参考文献：")
            lines.append("")
            for i, ref in enumerate(references, 1):
                lines.append(f"[{i}] {ref}")

        return "\n".join(lines)


if __name__ == "__main__":
    import asyncio
    from tools.pubmed_search import PubmedSearchTool
    from tools.gene_db_search import GeneDBSearchTool
    from tools.personal_lib_search import PersonalLibSearchTool

    # 创建简单的 mock 对象用于测试
    class MockRetriever:
        def search(self, query: str, top_k: int = 20):
            # 模拟基因库检索结果（同步方法，和真实 JinaRetriever 一致）
            class MockChunk:
                def __init__(self, title, gene):
                    self.paper_title = title
                    self.content = f"Mock gene content about {gene} in vitamin biosynthesis pathway."
                    self.doi = "10.1234/mock.doi"
                    self.gene_name = gene
                    self.gene_type = "enzyme"
                    self.journal = "Nature Biotechnology"

            return [
                (MockChunk("Vitamin C pathway in rice", "VitC1"), 0.85),
                (MockChunk("Carotenoid synthesis genes", "PSY1"), 0.75),
            ]

    class MockReranker:
        def rerank(self, query: str, documents: list[dict], top_n: int = 10):
            # 简单按原始 score 排序（同步方法，和真实 JinaReranker 一致）
            sorted_docs = sorted(documents, key=lambda x: x.get("score", 0), reverse=True)
            return sorted_docs[:top_n]

    # 初始化工具
    pubmed_tool = PubmedSearchTool()
    gene_db_tool = GeneDBSearchTool(retriever=MockRetriever())
    personal_lib_tool = PersonalLibSearchTool()  # 无 callback，search_raw 直接返回 []
    reranker = MockReranker()

    rag_tool = RAGSearchTool(
        sources={
            "pubmed": pubmed_tool,
            "gene_db": gene_db_tool,
            "personal_lib": personal_lib_tool,
        },
        reranker=reranker,
    )

    # 测试搜索
    print("=" * 60)
    print("测试 RAG 综合搜索工具")
    print("=" * 60)

    # 测试 1: 仅 PubMed
    print("\n[测试 1] 仅搜索 PubMed:")
    result1 = asyncio.run(rag_tool.execute(
        query="vitamin C biosynthesis rice",
        sources=["pubmed"],
        top_n=3
    ))
    print(result1)

    # 测试 2: PubMed + 基因库
    print("\n" + "=" * 60)
    print("[测试 2] 搜索 PubMed + 基因数据库:")
    result2 = asyncio.run(rag_tool.execute(
        query="carotenoid biosynthesis maize",
        sources=["pubmed", "gene_db"],
        top_n=5
    ))
    print(result2)

    # 测试 3: 查看 schema
    print("\n" + "=" * 60)
    print("[测试 3] Tool Schema:")
    import json
    print(json.dumps(rag_tool.schema, indent=2, ensure_ascii=False))
