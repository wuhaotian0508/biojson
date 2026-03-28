"""
Runnable example for TokenTracker.save_report

Demonstrates saving a detailed token usage report as a JSON file.

NOTE: The original TokenTracker.save_report has a deadlock bug: it acquires
self._lock and then calls self.get_summary(), which also tries to acquire
self._lock. Since threading.Lock is not reentrant, this deadlocks.
To demonstrate save_report working, we replace the lock with threading.RLock
(reentrant lock) before calling save_report.
"""

import json
import os
import sys
import tempfile
import threading

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


# --- Setup ---
tracker = TokenTracker(model="claude-3-opus")
tracker.add(MockResponse(MockUsage(5000, 2000, 7000)), stage="extraction", file="paper_01.md")
tracker.add(MockResponse(MockUsage(3000, 1500, 4500)), stage="verification", file="paper_01.md")

# Workaround: replace Lock with RLock to avoid the deadlock in save_report
tracker._lock = threading.RLock()

# --- Example 1: Save report to a temporary file (with subdirectory creation) ---
tmpdir = tempfile.mkdtemp()
report_path = os.path.join(tmpdir, "subdir", "token_report.json")
print(f"Saving report to: {report_path}")

returned_path = tracker.save_report(report_path)

assert os.path.isfile(report_path), "Report file was not created"
assert returned_path == report_path

# Read and inspect the saved report
with open(report_path, "r", encoding="utf-8") as f:
    report = json.load(f)

print(f"\nReport keys: {sorted(report.keys())}")
print(f"Model:       {report['model']}")
print(f"Num calls:   {len(report['calls'])}")
print(f"Summary keys: {sorted(report['summary'].keys())}")

assert report["model"] == "claude-3-opus"
assert len(report["calls"]) == 2
assert "timestamp" in report
assert "summary" in report
assert report["summary"]["total"]["prompt_tokens"] == 8000
assert report["summary"]["total"]["completion_tokens"] == 3500

print(f"\nFull report content:")
print(json.dumps(report, indent=2))

# --- Example 2: Save to a path in current directory (no subdirectory) ---
report_path_2 = os.path.join(tmpdir, "simple_report.json")
tracker.save_report(report_path_2)
assert os.path.isfile(report_path_2)

# Cleanup
os.remove(report_path)
os.rmdir(os.path.dirname(report_path))
os.remove(report_path_2)
os.rmdir(tmpdir)

print("\n[PASS] save_report() examples ran successfully.")
