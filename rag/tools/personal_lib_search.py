"""
个人知识库检索工具 — 封装 search/personal_lib.py 的 PersonalLibrary

功能：
  1. 用户上传的 PDF 文档向量检索
  2. 按 user_id 隔离（每个用户独立的知识库）
  3. 支持聚合检索（rag_search 调用）和独立检索（Agent 直接调用）

架构位置：
  - 独立调用：Agent 直接调用 personal_lib_search 工具
  - 聚合调用：rag_search 内部调用 search_raw，与 PubMed/基因库并行检索

数据流程：
  用户上传 PDF → PyMuPDF 解析 → 按页切块 → Jina Embeddings 向量化
  → 存储在 personal_lib/{user_id}/index/（chunks.pkl + embeddings.npy）
  → 查询时余弦相似度检索

与其他工具的区别：
  - pubmed_search: 联网搜索公开文献（无需登录）
  - gene_db_search: 搜索项目内置的基因数据库（全局共享）
  - personal_lib_search: 搜索用户上传的私有文档（需要 user_id）

注意：
  - 需要 user_id 参数（由 Agent 自动注入，不要手动填写）
  - 未登录用户或未配置回调时返回空结果
  - source_type 为 "personal"（不是 "personal_lib"，历史约定）
"""
import asyncio
import logging
from typing import ClassVar

from tools.base import BaseTool

logger = logging.getLogger(__name__)


class PersonalLibSearchTool(BaseTool):
    name = "personal_lib_search"
    description = "检索用户的个人知识库（上传的 PDF 文档）"
    # 注意：与 search/personal_lib.py:197 保持一致，source_type 用 "personal" 不是 "personal_lib"
    source_type: ClassVar[str] = "personal"

    def __init__(self, get_personal_lib=None, get_query_embedding=None):
        """
        初始化个人知识库检索工具。

        参数:
            get_personal_lib: user_id -> PersonalLibrary 的回调函数
                              - 由 app.py / server.py 注入
                              - 负责按 user_id 获取或创建 PersonalLibrary 实例
                              - 返回 None 表示用户未登录或库不存在
            get_query_embedding: query -> np.ndarray 的同步回调函数
                                 - 将查询文本转换为嵌入向量
                                 - 通常调用 search.embedding_utils.get_query_embedding
                                 - 返回 (dim,) 的 numpy 数组

        设计说明：
            - 使用回调而非直接依赖，避免循环导入
            - 回调为 None 时工具降级为空操作（返回空结果）
            - PersonalLibrary 实例由外部管理生命周期（缓存、清理等）
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

    async def search_raw(self, query: str, user_id: str | None = None,
                         top_k: int = 10, **_) -> list[dict]:
        """
        检索个人知识库，返回统一字典列表（供 rag_search 复用）。

        参数:
            query: 搜索查询文本
            user_id: 用户 ID（必需，由 Agent 自动注入）
            top_k: 返回结果数量（默认 10）

        返回:
            统一字典列表，每个元素包含：
              - source_type: "personal"（来源标识）
              - title: 文件名 + 页码（如 "paper.pdf (p.5)"）
              - content: chunk 文本内容
              - url: 空字符串（个人文档无公开链接）
              - score: 余弦相似度分数（0-1）
              - metadata: {filename, page, upload_time}

        工作流程：
            1. 校验 user_id 和回调函数（任一为空则返回 []）
            2. 调用 get_personal_lib(user_id) 获取用户的 PersonalLibrary 实例
            3. 调用 get_query_embedding(query) 获取查询向量
            4. 调用 lib.search(q_emb, top_k) 进行余弦相似度检索
            5. 返回结果（PersonalLibrary.search 已返回统一格式）

        异常处理：
            - 任何异常都捕获并记录警告日志
            - 返回空列表，不影响其他来源的检索
        """
        if not user_id or not self._get_lib or not self._get_embedding:
            return []
        try:
            lib = self._get_lib(user_id)
            if lib is None:
                return []
            q_emb = await asyncio.to_thread(self._get_embedding, query)
            return await asyncio.to_thread(lib.search, q_emb, top_k=top_k)
        except Exception as e:
            logger.warning("个人知识库检索失败: %s", e)
            return []

    async def execute(self, query: str, top_k: int = 10, user_id: str | None = None, **_) -> str:
        """
        检索个人知识库，返回格式化文本（供 Agent 直接阅读）。

        参数:
            query: 搜索查询文本
            top_k: 返回结果数量（默认 10）
            user_id: 用户 ID（必需，由 Agent 自动注入）

        返回:
            格式化的检索结果文本，包含：
              - Header: "个人知识库检索结果（共 N 条）："
              - 每条结果：
                  [1] filename.pdf (p.5)
                      chunk 文本内容...
              - 无来源标签（独立视图，与 rag_search 聚合视图不同）

        错误处理：
            - 未登录或未配置：返回 "个人知识库未配置或用户未登录。"
            - 检索失败：返回 "个人知识库检索失败: {错误信息}"
            - 无结果：返回 "在个人知识库中未找到与 '{query}' 相关的内容。"
        """
        from tools._formatters import render_personal

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
            lines.extend(render_personal(item, i, with_source_label=False))
            lines.append("")
        return "\n".join(lines)
