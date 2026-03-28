"""
TokenTracker.get_summary — Get a dict summarizing token usage grouped by stage, plus a total.

Source: extractor/token_tracker.py:59

Usage:
    python TokenTracker_get_summary.py
"""

# --- External Imports ---
import json
import threading
from datetime import datetime

# --- Target Class ---


class TokenTracker:
    """Thread-safe API token usage tracker."""

    def __init__(self, model="unknown"):
        self.model = model
        self.calls = []
        self._lock = threading.Lock()

    def add(self, response, stage="unknown", file=""):
        """(Inlined from token_tracker.py:22)"""
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
        """(Inlined from token_tracker.py:40)"""
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
        """Return a dict with per-stage aggregates and a 'total' key."""
        with self._lock:
            stages = sorted(set(c["stage"] for c in self.calls))
        summary = {}
        for stage in stages:
            summary[stage] = self._aggregate(stage)
        summary["total"] = self._aggregate()
        return summary


# --- Mock API Response ---


class _MockUsage:
    def __init__(self, prompt_tokens, completion_tokens, total_tokens):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens


class _MockResponse:
    def __init__(self, prompt_tokens, completion_tokens, total_tokens):
        self.usage = _MockUsage(prompt_tokens, completion_tokens, total_tokens)


# --- Sample Input ---
# Simulate a realistic extraction pipeline run with three stages:
#   extract  — pull gene data from the paper
#   verify   — validate the extracted JSON
#   classify — classify gene function category

responses = [
    (_MockResponse(4200, 1500, 5700), "extract",  "Mol_Plant_2016_Yang.md"),
    (_MockResponse(3800, 1200, 5000), "extract",  "Science_2003_Xie.md"),
    (_MockResponse(2100, 480,  2580), "verify",   "Mol_Plant_2016_Yang.md"),
    (_MockResponse(1900, 420,  2320), "verify",   "Science_2003_Xie.md"),
    (_MockResponse(800,  200,  1000), "classify",  "Mol_Plant_2016_Yang.md"),
]

# --- Run ---
if __name__ == "__main__":
    tracker = TokenTracker(model="claude-sonnet-4-20250514")

    for resp, stage, fname in responses:
        tracker.add(resp, stage=stage, file=fname)

    summary = tracker.get_summary()

    print("=== Token Usage Summary ===")
    print(json.dumps(summary, indent=2))
    print()

    # Show that the summary has one key per stage plus "total"
    print(f"Stages found: {[k for k in summary if k != 'total']}")
    print(f"Total calls:  {summary['total']['calls']}")
    print(f"Total tokens: {summary['total']['total_ktokens']} kT")
