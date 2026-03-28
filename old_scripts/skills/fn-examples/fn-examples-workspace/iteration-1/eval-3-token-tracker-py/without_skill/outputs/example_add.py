"""
Runnable example for TokenTracker.add

Demonstrates recording token usage from a mock API response object.
The method extracts .usage.prompt_tokens / .completion_tokens / .total_tokens
from the response and stores them as a record.
"""

import sys
sys.path.insert(0, "/data/haotianwu/biojson")

from extractor.token_tracker import TokenTracker


# --- Helper: mock objects to simulate an API response ---
class MockUsage:
    def __init__(self, prompt_tokens, completion_tokens, total_tokens):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens

class MockResponse:
    def __init__(self, usage):
        self.usage = usage


# --- Example 1: Add a normal response ---
tracker = TokenTracker(model="test-model")

response = MockResponse(MockUsage(
    prompt_tokens=500,
    completion_tokens=200,
    total_tokens=700,
))
tracker.add(response, stage="extraction", file="paper_01.md")

print("After adding one response:")
print(f"  Number of call records: {len(tracker.calls)}")
print(f"  Record: {tracker.calls[0]}")
assert len(tracker.calls) == 1
assert tracker.calls[0]["prompt_tokens"] == 500
assert tracker.calls[0]["completion_tokens"] == 200
assert tracker.calls[0]["total_tokens"] == 700
assert tracker.calls[0]["stage"] == "extraction"
assert tracker.calls[0]["file"] == "paper_01.md"

# --- Example 2: Add a second response with different stage ---
response2 = MockResponse(MockUsage(
    prompt_tokens=1000,
    completion_tokens=300,
    total_tokens=1300,
))
tracker.add(response2, stage="verification", file="paper_01.md")

print(f"\nAfter adding second response:")
print(f"  Number of call records: {len(tracker.calls)}")
assert len(tracker.calls) == 2

# --- Example 3: Response with no usage attribute (silently skipped) ---
class NoUsageResponse:
    pass

tracker.add(NoUsageResponse(), stage="extraction", file="paper_02.md")
print(f"\nAfter adding response with no usage:")
print(f"  Number of call records: {len(tracker.calls)}  (unchanged)")
assert len(tracker.calls) == 2  # still 2, nothing added

# --- Example 4: Default stage and file parameters ---
response3 = MockResponse(MockUsage(100, 50, 150))
tracker.add(response3)
print(f"\nAfter adding response with defaults:")
print(f"  Last record stage: {tracker.calls[-1]['stage']!r}")
print(f"  Last record file:  {tracker.calls[-1]['file']!r}")
assert tracker.calls[-1]["stage"] == "unknown"
assert tracker.calls[-1]["file"] == ""

print("\n[PASS] add() examples ran successfully.")
