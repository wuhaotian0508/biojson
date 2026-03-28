"""
TokenTracker.save_report — Save a detailed JSON usage report to disk.

Source: extractor/token_tracker.py:85

Note: The original code uses threading.Lock and calls get_summary() inside a
locked section, which causes a deadlock. This example uses threading.RLock
(reentrant lock) so that the nested lock acquisition works correctly, matching
the original code's intended behavior.

Usage:
    python TokenTracker_save_report.py
"""

# --- External Imports ---
import json
import os
import tempfile
import threading
from datetime import datetime

# --- Target Class ---


class TokenTracker:
    """Thread-safe API token usage tracker.

    Uses RLock to allow reentrant locking (save_report -> get_summary).
    """

    def __init__(self, model="unknown"):
        self.model = model
        self.calls = []
        # RLock instead of Lock to handle save_report calling get_summary
        # while already holding the lock.
        self._lock = threading.RLock()

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

    def _aggregate(self, stage_filter=None):
        """(Inlined from token_tracker.py:40)"""
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

    def get_summary(self):
        """(Inlined from token_tracker.py:59)"""
        with self._lock:
            stages = sorted(set(c["stage"] for c in self.calls))
        summary = {}
        for stage in stages:
            summary[stage] = self._aggregate(stage)
        summary["total"] = self._aggregate()
        return summary

    def save_report(self, path):
        """Save detailed usage report as JSON."""
        path = str(path)
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)

        with self._lock:
            report = {
                "timestamp": datetime.now().replace(microsecond=0).isoformat(),
                "model": self.model,
                "calls": list(self.calls),
                "summary": self.get_summary(),
            }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"  💾 Token report saved: {path}")
        return path


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
# Simulate a pipeline run, then save the report to a temp file so the example
# doesn't leave files scattered in the working directory.

responses = [
    (_MockResponse(4200, 1500, 5700), "extract", "Mol_Plant_2016_Yang.md"),
    (_MockResponse(2100, 480,  2580), "verify",  "Mol_Plant_2016_Yang.md"),
]

# --- Run ---
if __name__ == "__main__":
    tracker = TokenTracker(model="claude-sonnet-4-20250514")

    for resp, stage, fname in responses:
        tracker.add(resp, stage=stage, file=fname)

    # Save to a temporary file to keep the example self-contained
    tmp_dir = tempfile.mkdtemp(prefix="token_report_")
    report_path = os.path.join(tmp_dir, "pipeline_report.json")

    saved_path = tracker.save_report(report_path)

    # Read and display the saved report
    with open(saved_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    print("\n=== Saved Report Contents ===")
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # Clean up
    os.remove(saved_path)
    os.rmdir(tmp_dir)
    print(f"\n(Temporary file cleaned up)")
