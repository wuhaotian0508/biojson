"""
TokenTracker.merge — Merge another TokenTracker's records into this one (thread-safe).

Source: extractor/token_tracker.py:104

Usage:
    python TokenTracker_merge.py
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

    def merge(self, other):
        """Merge another TokenTracker's records (thread-safe)."""
        if isinstance(other, TokenTracker):
            with self._lock:
                with other._lock:
                    self.calls.extend(other.calls)


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
# In a parallel pipeline, each worker thread might have its own TokenTracker.
# After all threads finish, the main tracker merges them to get totals.

# Worker 1 processed two papers
worker1_responses = [
    (_MockResponse(4200, 1500, 5700), "extract", "Mol_Plant_2016_Yang.md"),
    (_MockResponse(3800, 1200, 5000), "extract", "Science_2003_Xie.md"),
]

# Worker 2 processed one paper
worker2_responses = [
    (_MockResponse(5100, 1800, 6900), "extract", "Nat_Commun_2023_Wang.md"),
]

# --- Run ---
if __name__ == "__main__":
    # Create per-worker trackers (as would happen in threaded processing)
    worker1_tracker = TokenTracker(model="claude-sonnet-4-20250514")
    for resp, stage, fname in worker1_responses:
        worker1_tracker.add(resp, stage=stage, file=fname)

    worker2_tracker = TokenTracker(model="claude-sonnet-4-20250514")
    for resp, stage, fname in worker2_responses:
        worker2_tracker.add(resp, stage=stage, file=fname)

    # Main tracker collects everything
    main_tracker = TokenTracker(model="claude-sonnet-4-20250514")

    print(f"Before merge: main has {len(main_tracker.calls)} calls")

    main_tracker.merge(worker1_tracker)
    print(f"After merging worker1: main has {len(main_tracker.calls)} calls")

    main_tracker.merge(worker2_tracker)
    print(f"After merging worker2: main has {len(main_tracker.calls)} calls")

    # Show all merged records
    print("\n=== Merged Call Records ===")
    for i, call in enumerate(main_tracker.calls):
        print(f"  [{i+1}] stage={call['stage']:<10} file={call['file']:<30} tokens={call['total_tokens']}")

    # Demonstrate that merging a non-TokenTracker object is a no-op
    main_tracker.merge({"not": "a tracker"})
    print(f"\nAfter merging a dict (no-op): main still has {len(main_tracker.calls)} calls")
