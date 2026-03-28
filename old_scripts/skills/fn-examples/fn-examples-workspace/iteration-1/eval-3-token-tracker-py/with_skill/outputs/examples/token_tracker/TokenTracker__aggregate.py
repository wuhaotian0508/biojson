"""
TokenTracker._aggregate — Aggregate token stats, optionally filtered by stage.

Source: extractor/token_tracker.py:40

Usage:
    python TokenTracker__aggregate.py
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
        """Record token usage from an API response (thread-safe).
        (Inlined from token_tracker.py:22 — needed to populate calls.)"""
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
# Three API calls across two pipeline stages:
#   - Two "extract" calls (processing two different papers)
#   - One "verify" call (validation pass on the first paper)

responses = [
    (_MockResponse(4200, 1500, 5700), "extract", "Mol_Plant_2016_Yang.md"),
    (_MockResponse(3800, 1200, 5000), "extract", "Science_2003_Xie.md"),
    (_MockResponse(2100, 480, 2580),  "verify",  "Mol_Plant_2016_Yang.md"),
]

# --- Run ---
if __name__ == "__main__":
    tracker = TokenTracker(model="claude-sonnet-4-20250514")

    for resp, stage, fname in responses:
        tracker.add(resp, stage=stage, file=fname)

    # Aggregate all calls (no filter)
    all_stats = tracker._aggregate()
    print("=== All Calls (no filter) ===")
    print(json.dumps(all_stats, indent=2))

    # Aggregate only the "extract" stage
    extract_stats = tracker._aggregate(stage_filter="extract")
    print("\n=== Extract Stage Only ===")
    print(json.dumps(extract_stats, indent=2))

    # Aggregate only the "verify" stage
    verify_stats = tracker._aggregate(stage_filter="verify")
    print("\n=== Verify Stage Only ===")
    print(json.dumps(verify_stats, indent=2))
