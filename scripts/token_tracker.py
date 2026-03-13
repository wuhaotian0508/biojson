"""
token_tracker.py
追踪 API Token 用量，支持多次调用累计，以 kTokens 为单位汇总。

用法:
    from token_tracker import TokenTracker
    tracker = TokenTracker(model="Vendor2/Claude-4.6-opus")
    
    # API 调用后
    response = client.chat.completions.create(...)
    tracker.add(response, stage="extract", file="xxx.md")
    
    # 脚本结束时
    tracker.print_summary()
    tracker.save_report("reports/token_usage_xxx.json")
"""

import json
import os
from datetime import datetime


class TokenTracker:
    """追踪 API Token 用量"""

    def __init__(self, model="unknown"):
        self.model = model
        self.calls = []  # 每次调用的详细记录

    def add(self, response, stage="unknown", file="", gene=""):
        """
        从 API response 中提取 token 用量并记录。
        
        Args:
            response: OpenAI API 返回的 response 对象
            stage: 阶段标识，如 "extract" 或 "verify"
            file: 处理的文件名
            gene: 验证的基因名（仅 verify 阶段使用）
        """
        usage = getattr(response, "usage", None)
        if usage is None:
            print(f"  ⚠️  Token 用量不可用 (stage={stage}, file={file})")
            return

        record = {
            "stage": stage,
            "file": file,
            "prompt_tokens": usage.prompt_tokens or 0,
            "completion_tokens": usage.completion_tokens or 0,
            "total_tokens": usage.total_tokens or 0,
            "timestamp": datetime.now().isoformat(),
        }
        if gene:
            record["gene"] = gene

        self.calls.append(record)

    def _aggregate(self, stage_filter=None):
        """按阶段聚合统计"""
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
        """获取完整的汇总数据"""
        stages = sorted(set(c["stage"] for c in self.calls))
        summary = {}
        for stage in stages:
            summary[stage] = self._aggregate(stage)
        summary["total"] = self._aggregate()
        return summary

    def print_summary(self):
        """打印格式化的用量汇总"""
        if not self.calls:
            print("\n📊 Token 用量: 无 API 调用记录")
            return

        summary = self.get_summary()
        stages = [s for s in summary if s != "total"]

        print(f"\n{'═' * 60}")
        print(f"📊 API Token 用量汇总 (模型: {self.model})")
        print(f"{'═' * 60}")
        print(f"  {'阶段':<12} {'输入 (kT)':>10} {'输出 (kT)':>10} {'合计 (kT)':>10} {'调用次数':>8}")
        print(f"  {'─' * 12} {'─' * 10} {'─' * 10} {'─' * 10} {'─' * 8}")

        for stage in stages:
            s = summary[stage]
            print(f"  {stage:<12} {s['prompt_ktokens']:>10.2f} {s['completion_ktokens']:>10.2f} {s['total_ktokens']:>10.2f} {s['calls']:>8}")

        if len(stages) > 1:
            print(f"  {'─' * 12} {'─' * 10} {'─' * 10} {'─' * 10} {'─' * 8}")

        t = summary["total"]
        print(f"  {'总计':<12} {t['prompt_ktokens']:>10.2f} {t['completion_ktokens']:>10.2f} {t['total_ktokens']:>10.2f} {t['calls']:>8}")
        print(f"{'═' * 60}")

    def save_report(self, path):
        """保存详细用量报告为 JSON"""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)

        report = {
            "timestamp": datetime.now().isoformat(),
            "model": self.model,
            "calls": self.calls,
            "summary": self.get_summary(),
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"  💾 Token 用量报告已保存: {path}")
        return path

    def merge(self, other):
        """合并另一个 TokenTracker 的记录"""
        if isinstance(other, TokenTracker):
            self.calls.extend(other.calls)


# ─── 全局单例（方便跨模块共享）─────────────────────────────────────────────────
_global_tracker = None


def get_tracker(model="unknown"):
    """获取全局 TokenTracker 单例"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = TokenTracker(model=model)
    return _global_tracker


def reset_tracker():
    """重置全局 tracker"""
    global _global_tracker
    _global_tracker = None
