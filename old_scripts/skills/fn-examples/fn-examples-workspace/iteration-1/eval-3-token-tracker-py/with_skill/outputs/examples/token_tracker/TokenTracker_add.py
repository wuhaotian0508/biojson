"""
TokenTracker.add — Record token usage from an API response (thread-safe).

Source: extractor/token_tracker.py:22

Usage:
    python TokenTracker_add.py
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
        """Record token usage from an API response (thread-safe)."""
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


# --- Mock API Response ---
# The `add` method expects an object with a `.usage` attribute that has
# `prompt_tokens`, `completion_tokens`, and `total_tokens` fields, similar
# to the response objects returned by OpenAI-compatible APIs.


class _MockUsage:
    """Simulates the usage sub-object on an API response."""
    def __init__(self, prompt_tokens, completion_tokens, total_tokens):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens


class _MockResponse:
    """Simulates an API response with a .usage attribute."""
    def __init__(self, prompt_tokens, completion_tokens, total_tokens):
        self.usage = _MockUsage(prompt_tokens, completion_tokens, total_tokens)


# --- Sample Input ---
# Simulate two API calls during a gene-extraction pipeline:
#   1) The "extract" stage processes a paper and uses ~4k input + ~1.5k output tokens.
#   2) The "verify" stage checks the extraction and uses ~2k input + ~500 output tokens.

response_extract = _MockResponse(
    prompt_tokens=4200,
    completion_tokens=1500,
    total_tokens=5700,
)

response_verify = _MockResponse(
    prompt_tokens=2100,
    completion_tokens=480,
    total_tokens=2580,
)

# --- Run ---
if __name__ == "__main__":
    tracker = TokenTracker(model="claude-sonnet-4-20250514")

    tracker.add(response_extract, stage="extract", file="Mol_Plant_2016_Yang.md")
    tracker.add(response_verify, stage="verify", file="Mol_Plant_2016_Yang.md")

    print("=== Recorded Calls ===")
    for i, call in enumerate(tracker.calls):
        print(f"\nCall {i + 1}:")
        for k, v in call.items():
            print(f"  {k:>20}: {v}")

    # Also demonstrate: a response with no .usage attribute is silently ignored
    tracker.add("plain_string_without_usage", stage="extract", file="bad.md")
    print(f"\nTotal calls after adding response without usage: {len(tracker.calls)}  (still 2)")
