"""
SearchSource — RAGSearchTool 可聚合的搜索来源协议

本协议抽取了 rag_search 对底层原子搜索工具的最小依赖:
  1. `source_type` 类属性,用于在 _formatters.RENDERERS 里查 renderer。
  2. `search_raw(query, **kwargs) -> list[dict]`,返回统一字典结构:
       {
         "source_type": str,
         "title": str,
         "content": str,
         "url": str,
         "score": float,
         "metadata": dict,   # source-specific extras
       }

只要任意类(不一定要继承 BaseTool)实现了这两个属性/方法,就可以作为 source
注入到 RAGSearchTool(sources=...) 里,不需要改动 rag_search 本体。

新增来源的完整步骤:
  1. 写一个类实现 `search_raw` 和 `source_type`(通常同时继承 BaseTool 以便独立暴露给 LLM)。
  2. 在 `tools/_formatters.py` 里写一个 `render_<src>` 并注册到 `RENDERERS`。
  3. 在 `app.py` / `server.py` 的 `sources` dict 里加一行。
"""
from __future__ import annotations

from typing import ClassVar, Protocol, runtime_checkable


@runtime_checkable
class SearchSource(Protocol):
    """RAGSearchTool 聚合检索所依赖的最小协议。

    注意:此处不约束 `search_raw` 的关键字参数,由 RAGSearchTool 按 source_type
    决定要注入哪些(例如仅 personal_lib 需要 user_id)。
    """

    source_type: ClassVar[str]

    async def search_raw(self, query: str, **kwargs) -> list[dict]:
        """返回统一字典结构的检索结果列表。失败时应返回 [],而非抛异常。"""
        ...
