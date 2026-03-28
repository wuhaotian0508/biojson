"""
TokenTracker.__init__ — Initialize a thread-safe API token usage tracker.

Source: extractor/token_tracker.py:17

Usage:
    python TokenTracker___init__.py
"""

# --- External Imports ---
import threading

# --- Target Class (minimal for __init__) ---


class TokenTracker:
    """Thread-safe API token usage tracker."""

    def __init__(self, model="unknown"):
        self.model = model
        self.calls = []
        self._lock = threading.Lock()


# --- Sample Input ---
# Typically you'd pass the model name used for the extraction pipeline,
# e.g. the LLM model identifier from your API configuration.

model_name = "claude-sonnet-4-20250514"

# --- Run ---
if __name__ == "__main__":
    # Create a tracker for a specific model
    tracker = TokenTracker(model=model_name)

    print("=== TokenTracker Initialized ===")
    print(f"  model:       {tracker.model}")
    print(f"  calls:       {tracker.calls}  (empty list)")
    print(f"  _lock type:  {type(tracker._lock).__name__}")

    # Also demonstrate default model name
    tracker_default = TokenTracker()
    print(f"\n  Default model: {tracker_default.model!r}")
