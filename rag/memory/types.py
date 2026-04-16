"""记忆系统数据模型定义"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

MemoryCategory = Literal["preference", "fact", "decision", "entity", "other"]

# 类别中文标签
CATEGORY_LABELS: dict[str, str] = {
    "preference": "偏好",
    "fact": "事实",
    "decision": "决策",
    "entity": "实体",
    "other": "其他",
}


@dataclass
class MemoryEntry:
    """单条记忆记录"""

    id: str
    content: str
    category: MemoryCategory = "other"
    importance: float = 0.5
    source: str = "auto"        # auto / manual
    created_at: float = 0.0     # unix timestamp
    updated_at: float = 0.0
    access_count: int = 0
    score: float = 0.0          # 检索时计算，不持久化

    @property
    def category_label(self) -> str:
        return CATEGORY_LABELS.get(self.category, self.category)


@dataclass
class MemoryConfig:
    """记忆系统配置"""

    enabled: bool = True
    db_path: str = "./data/memory/memories.db"
    auto_capture: bool = True
    auto_recall: bool = True
    recall_limit: int = 5
    max_memories: int = 500
    time_decay_rate: float = 0.01   # 每天衰减 1%
    dedup_threshold: float = 0.90   # 90% 相似度视为重复
