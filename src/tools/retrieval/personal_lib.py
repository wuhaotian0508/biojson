from __future__ import annotations

import asyncio
import logging
from typing import ClassVar

from tools import BaseTool
from tools.retrieval.formatters import render_personal

logger = logging.getLogger(__name__)


class PersonalLibSearchTool(BaseTool):
    name = "personal_lib_search"
    description = "检索用户的个人知识库（上传的 PDF 文档）"
    source_type: ClassVar[str] = "personal"

    def __init__(self, get_personal_lib=None, get_query_embedding=None):
        self._get_lib = get_personal_lib
        self._get_embedding = get_query_embedding

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
                            "description": "搜索查询文本",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "返回结果数量，默认 10",
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

    async def search_raw(
        self,
        query: str,
        user_id: str | None = None,
        top_k: int = 10,
        **_,
    ) -> list[dict]:
        if not user_id or not self._get_lib or not self._get_embedding:
            return []
        try:
            library = self._get_lib(user_id)
            if library is None:
                return []
            query_embedding = await asyncio.to_thread(self._get_embedding, query)
            return await asyncio.to_thread(library.search, query_embedding, top_k=top_k)
        except Exception as exc:
            logger.warning("Personal library search failed: %s", exc)
            return []

    async def execute(
        self,
        query: str,
        top_k: int = 10,
        user_id: str | None = None,
        **_,
    ) -> str:
        if not user_id or not self._get_lib or not self._get_embedding:
            return "个人知识库未配置或用户未登录。"
        try:
            library = self._get_lib(user_id)
            query_embedding = await asyncio.to_thread(self._get_embedding, query)
            results = await asyncio.to_thread(library.search, query_embedding, top_k=top_k)
        except Exception as exc:
            logger.warning("Personal library search failed: %s", exc)
            return f"个人知识库检索失败: {exc}"
        if not results:
            return f"在个人知识库中未找到与 '{query}' 相关的内容。"
        lines = [f"个人知识库检索结果（共 {len(results)} 条）：\n"]
        for index, item in enumerate(results, 1):
            lines.extend(render_personal(item, index, with_source_label=False))
            lines.append("")
        return "\n".join(lines)
