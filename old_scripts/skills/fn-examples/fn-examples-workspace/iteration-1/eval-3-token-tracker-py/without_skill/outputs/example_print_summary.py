"""
Runnable example for TokenTracker.print_summary

Demonstrates printing token usage summaries to stdout.
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


# --- Example 1: Print summary when there are no calls ---
print("=== Example 1: Empty tracker ===")
empty_tracker = TokenTracker(model="claude-3-opus")
empty_tracker.print_summary()
# Expected output: "Token usage: no API calls recorded"

# --- Example 2: Print summary with recorded calls ---
print("\n=== Example 2: Tracker with data ===")
tracker = TokenTracker(model="claude-3-opus")

tracker.add(MockResponse(MockUsage(5000, 2000, 7000)), stage="extraction", file="paper_01.md")
tracker.add(MockResponse(MockUsage(3000, 1500, 4500)), stage="extraction", file="paper_02.md")
tracker.add(MockResponse(MockUsage(1000, 500, 1500)), stage="verification", file="paper_01.md")

tracker.print_summary()
# Expected output shows:
#   Input:   9.00 kT
#   Output:  4.00 kT
#   Total:  13.00 kT
#   Calls:  3

print("\n[PASS] print_summary() examples ran successfully.")
