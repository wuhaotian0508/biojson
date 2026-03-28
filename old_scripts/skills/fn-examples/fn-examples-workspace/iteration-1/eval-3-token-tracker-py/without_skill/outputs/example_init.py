"""
Runnable example for TokenTracker.__init__

Demonstrates creating a TokenTracker instance with default and custom model names.
"""

import sys
sys.path.insert(0, "/data/haotianwu/biojson")

from extractor.token_tracker import TokenTracker


# Example 1: Default model name
tracker_default = TokenTracker()
print(f"Default model:  {tracker_default.model!r}")
print(f"Calls list:     {tracker_default.calls}")
assert tracker_default.model == "unknown"
assert tracker_default.calls == []

# Example 2: Custom model name
tracker_custom = TokenTracker(model="claude-3-opus")
print(f"\nCustom model:   {tracker_custom.model!r}")
print(f"Calls list:     {tracker_custom.calls}")
assert tracker_custom.model == "claude-3-opus"
assert tracker_custom.calls == []

print("\n[PASS] __init__ examples ran successfully.")
