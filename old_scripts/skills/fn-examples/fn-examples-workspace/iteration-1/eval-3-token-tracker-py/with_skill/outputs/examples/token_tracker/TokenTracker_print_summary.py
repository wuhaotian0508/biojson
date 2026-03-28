"""
TokenTracker.print_summary — Print a formatted table of total token usage and call count.

Source: extractor/token_tracker.py:68

Usage:
    python TokenTracker_print_summary.py
"""

# --- External Imports ---
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

    def print_summary(self):
        """Print total input/output/total tokens + call count."""
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
# Two extraction calls simulating a pipeline run on plant nutrient metabolism papers.

responses = [
    (_MockResponse(4200, 1500, 5700), "extract", "Mol_Plant_2016_Yang.md"),
    (_MockResponse(3800, 1200, 5000), "extract", "Science_2003_Xie.md"),
]

# --- Run ---
if __name__ == "__main__":
    # First: show output when no calls have been recorded
    empty_tracker = TokenTracker(model="claude-sonnet-4-20250514")
    print("--- Empty tracker ---")
    empty_tracker.print_summary()

    # Second: show output with populated data
    tracker = TokenTracker(model="claude-sonnet-4-20250514")
    for resp, stage, fname in responses:
        tracker.add(resp, stage=stage, file=fname)

    print("\n--- Populated tracker ---")
    tracker.print_summary()
