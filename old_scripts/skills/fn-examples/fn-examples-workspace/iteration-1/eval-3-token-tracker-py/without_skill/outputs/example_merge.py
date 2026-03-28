"""
Runnable example for TokenTracker.merge

Demonstrates merging one TokenTracker's records into another.
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


# --- Setup: create two separate trackers ---
tracker_a = TokenTracker(model="model-a")
tracker_a.add(MockResponse(MockUsage(500, 200, 700)), stage="extraction", file="paper_01.md")
tracker_a.add(MockResponse(MockUsage(600, 250, 850)), stage="extraction", file="paper_02.md")

tracker_b = TokenTracker(model="model-b")
tracker_b.add(MockResponse(MockUsage(300, 100, 400)), stage="verification", file="paper_01.md")
tracker_b.add(MockResponse(MockUsage(400, 150, 550)), stage="verification", file="paper_02.md")

print(f"tracker_a calls before merge: {len(tracker_a.calls)}")
print(f"tracker_b calls before merge: {len(tracker_b.calls)}")

# --- Example 1: Merge tracker_b into tracker_a ---
tracker_a.merge(tracker_b)

print(f"\ntracker_a calls after merge:  {len(tracker_a.calls)}")
print(f"tracker_b calls after merge:  {len(tracker_b.calls)}  (unchanged)")

assert len(tracker_a.calls) == 4
assert len(tracker_b.calls) == 2  # source tracker is not modified

# Verify the merged records
agg = tracker_a._aggregate()
print(f"\ntracker_a aggregate after merge:")
print(f"  prompt_tokens:     {agg['prompt_tokens']}")
print(f"  completion_tokens: {agg['completion_tokens']}")
print(f"  total_tokens:      {agg['total_tokens']}")
print(f"  calls:             {agg['calls']}")

assert agg["prompt_tokens"] == 500 + 600 + 300 + 400  # 1800
assert agg["completion_tokens"] == 200 + 250 + 100 + 150  # 700
assert agg["total_tokens"] == 700 + 850 + 400 + 550  # 2500
assert agg["calls"] == 4

# --- Example 2: Merge with a non-TokenTracker object (no-op) ---
tracker_c = TokenTracker(model="model-c")
tracker_c.add(MockResponse(MockUsage(100, 50, 150)), stage="test")
calls_before = len(tracker_c.calls)

tracker_c.merge("not a tracker")  # should be silently ignored
tracker_c.merge(42)               # should be silently ignored
tracker_c.merge(None)             # should be silently ignored

assert len(tracker_c.calls) == calls_before
print(f"\nMerging non-TokenTracker objects: calls unchanged ({len(tracker_c.calls)})")

# --- Example 3: Merge an empty tracker ---
empty_tracker = TokenTracker()
tracker_c.merge(empty_tracker)
assert len(tracker_c.calls) == calls_before
print(f"Merging empty tracker: calls unchanged ({len(tracker_c.calls)})")

print("\n[PASS] merge() examples ran successfully.")
