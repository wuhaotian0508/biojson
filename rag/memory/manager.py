"""记忆管理器 — 业务逻辑层

负责自动捕获、自动召回和工具 API。
"""

from __future__ import annotations

import logging
import re

from .store import MemoryStore
from .types import MemoryCategory, MemoryConfig, MemoryEntry

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# 自动捕获规则
# ------------------------------------------------------------------

CAPTURE_PATTERNS: list[tuple[re.Pattern, MemoryCategory]] = [
    # 中文 — 明确记忆指令
    (re.compile(r"记住[：:\s].+", re.S), "fact"),
    (re.compile(r"请?记住.+"), "fact"),
    # 中文 — 偏好
    (re.compile(r"我(喜欢|偏好|习惯|倾向于|一般用|经常用|更喜欢)"), "preference"),
    (re.compile(r"以后(都|总是|一直|请|帮我)"), "preference"),
    (re.compile(r"(每次|下次|将来)(都|请|帮我)"), "preference"),
    (re.compile(r"不要(再|总是|每次)"), "preference"),
    # 中文 — 事实
    (re.compile(r"我的.{1,15}(是|叫|为|用的是)"), "fact"),
    (re.compile(r"我(是|叫|在|住在|来自|从事|负责|管理)"), "fact"),
    # 中文 — 决策
    (re.compile(r"我(决定|选择|确定|打算)(了|要)?"), "decision"),
    # English
    (re.compile(r"(?i)\bremember\b.+"), "fact"),
    (re.compile(r"(?i)\bi (prefer|like|love|hate|always|never|usually)\b"), "preference"),
    (re.compile(r"(?i)\bmy .{1,30} is\b"), "fact"),
    (re.compile(r"(?i)\bi('m| am| work| live)\b"), "fact"),
    (re.compile(r"(?i)\bi (decided|chose|will use|want to use)\b"), "decision"),
]

_MIN_CAPTURE_LEN = 6
_MAX_CAPTURE_LEN = 500


class MemoryManager:
    """记忆管理器

    Args:
        config: 记忆系统配置
    """

    def __init__(self, config: MemoryConfig):
        self.config = config
        self._store = MemoryStore(config)

    @property
    def store(self) -> MemoryStore:
        return self._store

    # ------------------------------------------------------------------
    # 自动召回 — 注入系统提示词
    # ------------------------------------------------------------------

    async def recall_for_context(self, query: str) -> str:
        """基于用户消息搜索相关记忆，返回格式化的上下文文本块。

        无记忆时返回空字符串。
        """
        if not self.config.auto_recall:
            return ""

        entries = await self._store.search(query, limit=self.config.recall_limit)
        if not entries:
            return ""

        lines = [
            "<relevant_memories>",
            "以下是关于用户的历史记忆，可作为回答参考：",
        ]
        for e in entries:
            lines.append(f"- [{e.category_label}] {e.content}")
        lines.append("</relevant_memories>")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 自动捕获 — 正则匹配
    # ------------------------------------------------------------------

    async def auto_capture(self, message: str) -> list[str]:
        """从用户消息中提取值得记忆的内容（正则匹配）。

        返回新保存的记忆内容列表。
        """
        if not self.config.auto_capture:
            return []

        message = message.strip()
        if len(message) < _MIN_CAPTURE_LEN or len(message) > _MAX_CAPTURE_LEN:
            return []

        saved: list[str] = []
        for pattern, category in CAPTURE_PATTERNS:
            if pattern.search(message):
                memory_id = await self._store.add(
                    content=message,
                    category=category,
                    importance=0.6,
                    source="auto",
                )
                if memory_id:
                    saved.append(message)
                    await self._enforce_limit()
                break  # 单条消息最多匹配一次

        return saved

    # ------------------------------------------------------------------
    # 工具 API
    # ------------------------------------------------------------------

    async def search(
        self, query: str, limit: int = 5, category: str | None = None
    ) -> list[MemoryEntry]:
        """搜索记忆（memory_search 工具调用）"""
        results = await self._store.search(query, limit=limit)
        if category:
            results = [r for r in results if r.category == category]
        return results

    async def save(
        self, content: str, category: str = "other", importance: float = 0.8
    ) -> str | None:
        """手动保存记忆（memory_save 工具调用）"""
        memory_id = await self._store.add(
            content=content,
            category=category,
            importance=importance,
            source="manual",
        )
        await self._enforce_limit()
        return memory_id

    async def forget(self, query: str) -> int:
        """删除匹配的记忆（memory_forget 工具调用）"""
        return await self._store.delete_by_query(query)

    async def close(self) -> None:
        await self._store.close()

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    async def _enforce_limit(self) -> None:
        deleted = await self._store.enforce_limit()
        if deleted > 0:
            logger.info("记忆数量超限, 清理 %d 条", deleted)
