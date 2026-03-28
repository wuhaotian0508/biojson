"""
Runnable example for TokenTracker.get_summary

Demonstrates getting a per-stage and total summary of token usage.
"""

import sys
sys.path.insert(0, "/data/haotianwu/biojson")

from extractor.token_tracker import TokenTracker


# --- Helper: mock objects ---
class MockUsage:
    def __init__(self, prompt_tokens, completion_tokens, total_tokens):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens

class MockResponse:
    def __init__(self, usage):
        self.usage = usage


# --- Setup: add records across multiple stages ---
tracker = TokenTracker(model="test-model")

tracker.add(MockResponse(MockUsage(500, 200, 700)), stage="extraction", file="paper_01.md")
tracker.add(MockResponse(MockUsage(600, 250, 850)), stage="extraction", file="paper_02.md")
tracker.add(MockResponse(MockUsage(300, 100, 400)), stage="verification", file="paper_01.md")

# --- Example 1: Full summary ---
summary = tracker.get_summary()

print("Summary keys:", sorted(summary.keys()))
assert "extraction" in summary
assert "verification" in summary
assert "total" in summary

print("\nPer-stage breakdown:")
for stage_name, stats in summary.items():
    print(f"\n  [{stage_name}]")
    for k, v in stats.items():
        print(f"    {k}: {v}")

# Verify extraction stage
assert summary["extraction"]["prompt_tokens"] == 1100
assert summary["extraction"]["calls"] == 2

# Verify verification stage
assert summary["verification"]["prompt_tokens"] == 300
assert summary["verification"]["calls"] == 1

# Verify total
assert summary["total"]["prompt_tokens"] == 1400
assert summary["total"]["calls"] == 3

# --- Example 2: Empty tracker returns only "total" ---
empty_tracker = TokenTracker()
empty_summary = empty_tracker.get_summary()
print("\n\nEmpty tracker summary:", empty_summary)
assert "total" in empty_summary
assert empty_summary["total"]["calls"] == 0
assert empty_summary["total"]["prompt_tokens"] == 0

print("\n[PASS] get_summary() examples ran successfully.")
