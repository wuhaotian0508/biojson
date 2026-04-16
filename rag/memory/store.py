"""SQLite + FTS5 记忆存储层

单个 SQLite 文件存储所有记忆。FTS5 索引使用 jieba 分词预处理支持中文搜索。
同步 SQLite 操作通过 asyncio.to_thread 包装为异步接口。
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
import time
import uuid
from difflib import SequenceMatcher
from pathlib import Path

import jieba

from .types import MemoryConfig, MemoryEntry

logger = logging.getLogger(__name__)
jieba.setLogLevel(logging.WARNING)

_SCHEMA_SQL = """\
CREATE TABLE IF NOT EXISTS memories (
    id          TEXT PRIMARY KEY,
    content     TEXT NOT NULL,
    category    TEXT DEFAULT 'other',
    importance  REAL DEFAULT 0.5,
    source      TEXT DEFAULT 'auto',
    created_at  REAL NOT NULL,
    updated_at  REAL NOT NULL,
    access_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
CREATE INDEX IF NOT EXISTS idx_memories_updated ON memories(updated_at);
"""

_FTS_SQL = "CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(content);"


def _segment(text: str) -> str:
    """jieba 分词，返回空格分隔的结果"""
    return " ".join(jieba.cut(text))


class MemoryStore:
    """SQLite + FTS5 记忆存储

    FTS5 索引存储 jieba 分词后的文本，查询时也先分词再检索。
    """

    def __init__(self, config: MemoryConfig):
        self._config = config
        self._db_path = Path(config.db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = self._connect()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_schema(self) -> None:
        cur = self._conn.cursor()
        cur.executescript(_SCHEMA_SQL)
        # 确保 FTS 表存在
        try:
            cur.execute("SELECT * FROM memories_fts LIMIT 0")
        except sqlite3.OperationalError:
            cur.execute(_FTS_SQL)
            self._rebuild_fts_index(cur)
        self._conn.commit()

    def _rebuild_fts_index(self, cur: sqlite3.Cursor) -> None:
        cur.execute("DELETE FROM memories_fts")
        rows = cur.execute("SELECT rowid, content FROM memories").fetchall()
        for row in rows:
            cur.execute(
                "INSERT INTO memories_fts(rowid, content) VALUES (?, ?)",
                (row["rowid"], _segment(row["content"])),
            )
        logger.info("重建 FTS 索引: %d 条记录", len(rows))

    # ------------------------------------------------------------------
    # 异步公开接口（包装同步方法）
    # ------------------------------------------------------------------

    async def add(
        self,
        content: str,
        category: str = "other",
        importance: float = 0.5,
        source: str = "auto",
    ) -> str | None:
        return await asyncio.to_thread(
            self._add_sync, content, category, importance, source
        )

    async def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        return await asyncio.to_thread(self._search_sync, query, limit)

    async def get_recent(self, limit: int = 10) -> list[MemoryEntry]:
        return await asyncio.to_thread(self._get_recent_sync, limit)

    async def delete(self, memory_id: str) -> bool:
        return await asyncio.to_thread(self._delete_sync, memory_id)

    async def delete_by_query(self, query: str) -> int:
        return await asyncio.to_thread(self._delete_by_query_sync, query)

    async def count(self) -> int:
        return await asyncio.to_thread(self._count_sync)

    async def enforce_limit(self) -> int:
        return await asyncio.to_thread(self._enforce_limit_sync)

    async def close(self) -> None:
        await asyncio.to_thread(self._close_sync)

    # ------------------------------------------------------------------
    # 同步实现
    # ------------------------------------------------------------------

    def _add_sync(
        self,
        content: str,
        category: str,
        importance: float,
        source: str,
    ) -> str | None:
        content = content.strip()
        if not content:
            return None

        # 去重检查
        existing = self._search_sync(content, limit=1)
        if existing:
            sim = SequenceMatcher(None, content.lower(), existing[0].content.lower()).ratio()
            if sim >= self._config.dedup_threshold:
                logger.debug("重复记忆 (sim=%.2f), 更新时间戳: %s", sim, existing[0].id)
                self._conn.execute(
                    "UPDATE memories SET updated_at = ?, access_count = access_count + 1 WHERE id = ?",
                    (time.time(), existing[0].id),
                )
                self._conn.commit()
                return None

        now = time.time()
        memory_id = uuid.uuid4().hex[:16]
        segmented = _segment(content)

        self._conn.execute(
            "INSERT INTO memories (id, content, category, importance, source, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (memory_id, content, category, importance, source, now, now),
        )
        rowid = self._conn.execute(
            "SELECT rowid FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()["rowid"]
        self._conn.execute(
            "INSERT INTO memories_fts(rowid, content) VALUES (?, ?)",
            (rowid, segmented),
        )
        self._conn.commit()
        logger.info("保存记忆 %s: %s", memory_id, content[:80])
        return memory_id

    def _search_sync(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        query = query.strip()
        if not query:
            return self._get_recent_sync(limit)

        tokens = [t.strip() for t in jieba.cut(query) if t.strip()]
        if not tokens:
            return self._get_recent_sync(limit)

        fts_query = " OR ".join(f'"{t}"' for t in tokens)
        sql = """
            SELECT m.*, bm25(memories_fts) AS rank
            FROM memories m
            JOIN memories_fts ON memories_fts.rowid = m.rowid
            WHERE memories_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """
        rows = []
        try:
            rows = self._conn.execute(sql, (fts_query, limit * 2)).fetchall()
        except sqlite3.OperationalError:
            logger.debug("FTS 查询失败, 回退到 LIKE 搜索")

        if not rows:
            return self._search_like(query, limit)

        now = time.time()
        entries = []
        for row in rows:
            entry = self._row_to_entry(row)
            bm25 = abs(row["rank"])
            days = (now - entry.updated_at) / 86400
            decay = 1.0 / (1.0 + days * self._config.time_decay_rate)
            entry.score = bm25 * decay
            entries.append(entry)

        entries.sort(key=lambda e: e.score, reverse=True)
        return entries[:limit]

    def _search_like(self, query: str, limit: int) -> list[MemoryEntry]:
        tokens = [t.strip() for t in jieba.cut(query) if t.strip()]
        if not tokens:
            return self._get_recent_sync(limit)

        conditions = " OR ".join("content LIKE ?" for _ in tokens)
        params: list = [f"%{t}%" for t in tokens] + [limit]
        sql = f"SELECT * FROM memories WHERE ({conditions}) ORDER BY updated_at DESC LIMIT ?"
        rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def _get_recent_sync(self, limit: int = 10) -> list[MemoryEntry]:
        rows = self._conn.execute(
            "SELECT * FROM memories ORDER BY updated_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def _delete_sync(self, memory_id: str) -> bool:
        row = self._conn.execute(
            "SELECT rowid FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()
        if row:
            self._conn.execute("DELETE FROM memories_fts WHERE rowid = ?", (row["rowid"],))
        cur = self._conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def _delete_by_query_sync(self, query: str) -> int:
        matches = self._search_sync(query, limit=3)
        if not matches:
            return 0
        deleted = 0
        for m in matches:
            sim = SequenceMatcher(None, query.lower(), m.content.lower()).ratio()
            if sim >= 0.5:
                if self._delete_sync(m.id):
                    deleted += 1
        return deleted

    def _count_sync(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS cnt FROM memories").fetchone()
        return row["cnt"] if row else 0

    def _enforce_limit_sync(self) -> int:
        current = self._count_sync()
        if current <= self._config.max_memories:
            return 0
        to_delete = current - self._config.max_memories

        rows = self._conn.execute(
            "SELECT rowid FROM memories ORDER BY importance ASC, updated_at ASC LIMIT ?",
            (to_delete,),
        ).fetchall()
        if not rows:
            return 0

        rowids = [r["rowid"] for r in rows]
        ph = ",".join("?" for _ in rowids)
        self._conn.execute(f"DELETE FROM memories_fts WHERE rowid IN ({ph})", rowids)
        cur = self._conn.execute(f"DELETE FROM memories WHERE rowid IN ({ph})", rowids)
        self._conn.commit()
        logger.info("清理记忆: 删除 %d 条", cur.rowcount)
        return cur.rowcount

    def _close_sync(self) -> None:
        self._conn.close()

    @staticmethod
    def _row_to_entry(row: sqlite3.Row) -> MemoryEntry:
        return MemoryEntry(
            id=row["id"],
            content=row["content"],
            category=row["category"],
            importance=row["importance"],
            source=row["source"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            access_count=row["access_count"],
        )
