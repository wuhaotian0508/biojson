"""
基因数据库检索工具 — 封装 search/retriever.py 的 JinaRetriever

execute 返回可读文本（供 agent 直接阅读），而非结构化 dict。
"""
import asyncio


class GeneDBSearchTool:
    name = "gene_db_search"
    description = "检索本地基因数据库，基于向量相似度返回相关基因文献片段"

    def __init__(self, retriever):
        self._retriever = retriever

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
                            "description": "检索查询",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "返回结果数量，默认 20",
                        },
                    },
                    "required": ["query"],
                },
            },
        }

    async def execute(self, query: str, top_k: int = 20, **_) -> str:
        """调用 JinaRetriever.search()，返回格式化可读文本"""
        chunks = await asyncio.to_thread(self._retriever.search, query, top_k=top_k)
        if not chunks:
            return f"未找到与 '{query}' 相关的基因数据库记录。"
        return self._format_results(chunks)

    @staticmethod
    def _format_results(chunks) -> str:
        lines = [f"基因数据库检索结果（共 {len(chunks)} 条）：\n"]
        for i, (chunk, score) in enumerate(chunks, 1):
            lines.append(f"[{i}] {chunk.paper_title}")
            lines.append(f"    基因: {chunk.gene_name}")
            lines.append(f"    类型: {chunk.gene_type}")
            lines.append(f"    期刊: {chunk.journal}")
            if chunk.doi:
                lines.append(f"    DOI: {chunk.doi}")
            lines.append(f"    相关性: {score:.4f}")
            content = chunk.content
            if len(content) > 500:
                content = content[:500] + "..."
            lines.append(f"    内容: {content}")
            lines.append("")
        return "\n".join(lines)
