"""
token_tracker.py — Thread-safe API token usage tracker.

Simplified version: only prints total input/output/total tokens + call count.
Thread-safe for parallel paper processing.

[PR 改动 by 学长 muskliu - 2026-03-29]
- threading.Lock() → threading.RLock()（可重入锁）
  避免 save_report() 中 self._lock 嵌套调用 get_summary()（也用了 self._lock）导致死锁
- save_report() 中先复制 self.calls 再构建 report，避免锁内长时间操作
"""

import json
import os
import threading
from datetime import datetime


class TokenTracker:
    """Thread-safe API token usage tracker."""

    def __init__(self, model="unknown"):
        """初始化 token 追踪器。

        [PR 改动] self._lock 改为 threading.RLock()（可重入锁），
        防止同一线程在 save_report() 嵌套调用 get_summary() 时死锁。
        """
        self.model = model
        self.calls = []
        self._lock = threading.RLock()

    def add(self, response, stage="unknown", file=""):
        """记录一次 API 调用的 token 用量（线程安全）。

        从 response.usage 中提取 prompt_tokens/completion_tokens，
        加入总计并保存到明细列表。

        Args:
            response: OpenAI API 的响应对象
            stage: 调用阶段，如 "extract" / "verify" / "preprocess"
            file: 对应的论文文件名
        """
        usage = getattr(response, "usage", None)
        if usage is None:
            return

        record = {
            "stage": stage,
            "file": file,
            "prompt_tokens": usage.prompt_tokens or 0,
            "completion_tokens": usage.completion_tokens or 0,
            "total_tokens": usage.total_tokens or 0,
            "timestamp": datetime.now().isoformat(),
        }

        with self._lock:
            self.calls.append(record)

    def _aggregate(self, stage_filter=None):
        """Aggregate stats, optionally filtered by stage."""
        with self._lock:
            filtered = self.calls if stage_filter is None else [
                c for c in self.calls if c["stage"] == stage_filter
            ]
            prompt = sum(c["prompt_tokens"] for c in filtered)
            completion = sum(c["completion_tokens"] for c in filtered)
            total = sum(c["total_tokens"] for c in filtered)
        return {
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "total_tokens": total,
            "prompt_ktokens": round(prompt / 1000, 2),
            "completion_ktokens": round(completion / 1000, 2),
            "total_ktokens": round(total / 1000, 2),
            "calls": len(filtered),
        }

    def get_summary(self):
        with self._lock:
            stages = sorted(set(c["stage"] for c in self.calls))
        summary = {}
        for stage in stages:
            summary[stage] = self._aggregate(stage)
        summary["total"] = self._aggregate()
        return summary

    def print_summary(self):
        """打印 token 用量汇总（总 input/output/total + 调用次数）。"""
        with self._lock:
            if not self.calls:
                print("\n📊 Token usage: no API calls recorded")
                return

        t = self._aggregate()
        print(f"\n{'═' * 50}")
        print(f"📊 Token Usage (model: {self.model})")
        print(f"{'═' * 50}")
        print(f"  Input:  {t['prompt_ktokens']:>10.2f} kT")
        print(f"  Output: {t['completion_ktokens']:>10.2f} kT")
        print(f"  Total:  {t['total_ktokens']:>10.2f} kT")
        print(f"  Calls:  {t['calls']:>10}")
        print(f"{'═' * 50}")

    def save_report(self, path):
        """保存详细的 token 用量报告到 JSON 文件。

        [PR 改动] 先在锁内复制 self.calls 列表，避免长时间持锁。
        用 RLock 所以内部调用 get_summary() 不会死锁。
        """
        path = str(path)
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)

        with self._lock:
            calls = list(self.calls)
            report = {
                "timestamp": datetime.now().replace(microsecond=0).isoformat(),
                "model": self.model,
                "calls": calls,
                "summary": self.get_summary(),
            }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"  💾 Token report saved: {path}")
        return path

    def merge(self, other):
        """Merge another TokenTracker's records (thread-safe)."""
        if isinstance(other, TokenTracker):
            with self._lock:
                with other._lock:
                    self.calls.extend(other.calls)
