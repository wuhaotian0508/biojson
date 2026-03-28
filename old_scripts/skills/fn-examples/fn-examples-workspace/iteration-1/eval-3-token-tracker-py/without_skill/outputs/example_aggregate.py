"""
Runnable example for TokenTracker._aggregate

Demonstrates aggregating token stats, with and without a stage filter.
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


# --- Setup: add several records across two stages ---
tracker = TokenTracker(model="test-model")

tracker.add(MockResponse(MockUsage(500, 200, 700)), stage="extraction", file="paper_01.md")
tracker.add(MockResponse(MockUsage(600, 250, 850)), stage="extraction", file="paper_02.md")
tracker.add(MockResponse(MockUsage(300, 100, 400)), stage="verification", file="paper_01.md")

# --- Example 1: Aggregate all records (no filter) ---
agg_all = tracker._aggregate()
print("Aggregate all records (no stage filter):")
for k, v in agg_all.items():
    print(f"  {k}: {v}")

assert agg_all["prompt_tokens"] == 1400
assert agg_all["completion_tokens"] == 550
assert agg_all["total_tokens"] == 1950
assert agg_all["calls"] == 3
assert agg_all["prompt_ktokens"] == 1.4
assert agg_all["completion_ktokens"] == 0.55
assert agg_all["total_ktokens"] == 1.95

# --- Example 2: Aggregate filtered by "extraction" stage ---
agg_extraction = tracker._aggregate(stage_filter="extraction")
print("\nAggregate 'extraction' stage only:")
for k, v in agg_extraction.items():
    print(f"  {k}: {v}")

assert agg_extraction["prompt_tokens"] == 1100
assert agg_extraction["completion_tokens"] == 450
assert agg_extraction["total_tokens"] == 1550
assert agg_extraction["calls"] == 2

# --- Example 3: Aggregate filtered by "verification" stage ---
agg_verification = tracker._aggregate(stage_filter="verification")
print("\nAggregate 'verification' stage only:")
for k, v in agg_verification.items():
    print(f"  {k}: {v}")

assert agg_verification["prompt_tokens"] == 300
assert agg_verification["completion_tokens"] == 100
assert agg_verification["total_tokens"] == 400
assert agg_verification["calls"] == 1

# --- Example 4: Aggregate with non-existent stage returns zeros ---
agg_empty = tracker._aggregate(stage_filter="nonexistent")
print("\nAggregate 'nonexistent' stage:")
for k, v in agg_empty.items():
    print(f"  {k}: {v}")

assert agg_empty["prompt_tokens"] == 0
assert agg_empty["total_tokens"] == 0
assert agg_empty["calls"] == 0

print("\n[PASS] _aggregate() examples ran successfully.")
