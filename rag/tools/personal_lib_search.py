"""
个人知识库检索工具 — 封装 search/personal_lib.py 的 PersonalLibrary

改进：接受 query 字符串 + user_id，内部处理嵌入和库实例查找。
返回可读文本供 agent 直接阅读。
"""
import asyncio
import logging

from tools.base import BaseTool

logger = logging.getLogger(__name__)


class PersonalLibSearchTool(BaseTool):
    name = "personal_lib_search"
    description = "检索用户的个人知识库（上传的 PDF 文档）"

    def __init__(self, get_personal_lib=None, get_query_embedding=None):
        """
        参数:
            get_personal_lib:    user_id -> PersonalLibrary 的回调
            get_query_embedding: query -> np.ndarray 的同步回调
        """
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

    async def execute(self, query: str, top_k: int = 10, user_id: str | None = None, **_) -> str:
        """检索个人知识库，返回格式化文本"""
        if not user_id or not self._get_lib or not self._get_embedding:
            return "个人知识库未配置或用户未登录。"

        try:
            lib = self._get_lib(user_id)
            q_emb = await asyncio.to_thread(self._get_embedding, query)
            results = await asyncio.to_thread(lib.search, q_emb, top_k=top_k)
        except Exception as e:
            logger.warning("个人知识库检索失败: %s", e)
            return f"个人知识库检索失败: {e}"

        if not results:
            return f"在个人知识库中未找到与 '{query}' 相关的内容。"

        lines = [f"个人知识库检索结果（共 {len(results)} 条）：\n"]
        for i, item in enumerate(results, 1):
            meta = item.get("metadata", {})
            filename = meta.get("filename", "")
            page = meta.get("page", "")
            content = item.get("content", "")
            if len(content) > 500:
                content = content[:500] + "..."
            lines.append(f"[{i}] {filename} (p.{page})")
            lines.append(f"    {content}")
            lines.append("")
        return "\n".join(lines)
