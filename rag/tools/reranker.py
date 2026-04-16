"""
Reranker 工具 — 封装 search/reranker.py 的 JinaReranker
"""
import asyncio


class RerankerTool:
    name = "reranker"
    description = "使用 Jina Reranker 对候选结果进行语义重排序"

    def __init__(self, reranker):
        self._reranker = reranker

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
                            "description": "查询文本",
                        },
                        "candidates": {
                            "type": "array",
                            "description": "候选结果列表",
                            "items": {"type": "object"},
                        },
                        "top_n": {
                            "type": "integer",
                            "description": "保留排名前 N 的结果",
                        },
                    },
                    "required": ["query", "candidates", "top_n"],
                },
            },
        }

    async def execute(self, query: str, candidates: list, top_n: int, **_) -> list[dict]:
        """调用 JinaReranker.rerank()"""
        return await asyncio.to_thread(self._reranker.rerank, query, candidates, top_n)
