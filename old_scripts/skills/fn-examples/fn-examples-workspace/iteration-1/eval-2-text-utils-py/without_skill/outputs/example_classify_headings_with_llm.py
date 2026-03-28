#!/usr/bin/env python3
"""
Example: _classify_headings_with_llm()

Calls an LLM API to determine which section headings should be removed
from a scientific paper (e.g., Introduction, References, Acknowledgments).
Returns a set of 0-based indices of headings to remove.

Since this function requires a live LLM API, this example demonstrates
its behavior by mocking the API call. The mock simulates the LLM
returning a JSON array of indices to remove.

Signature:
    _classify_headings_with_llm(headings: list[str]) -> set[int] | None
"""
import sys, os
sys.path.insert(0, '/data/haotianwu/biojson')

from unittest.mock import patch, MagicMock

# We need to import the module first so it's in sys.modules,
# then patch the openai.OpenAI class that gets imported inside the function.
from extractor.text_utils import _classify_headings_with_llm


def make_mock_client(response_content=None, side_effect=None):
    """Helper to create a mock OpenAI client."""
    mock_client = MagicMock()
    if side_effect:
        mock_client.chat.completions.create.side_effect = side_effect
    else:
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = response_content
        mock_client.chat.completions.create.return_value = mock_resp
    return mock_client


# ── Example 1: Typical headings, LLM marks some for removal ─────────────────
headings = [
    "# Introduction",
    "# Results",
    "# Discussion",
    "# Methods",
    "# References",
    "# Acknowledgments",
]

mock_client1 = make_mock_client("[0, 4, 5]")

print("=== Example 1: Typical headings ===")
print("Input headings:")
for i, h in enumerate(headings):
    print(f"  {i}: {h}")

with patch("openai.OpenAI", return_value=mock_client1), \
     patch("dotenv.load_dotenv"), \
     patch.dict(os.environ, {"OPENAI_API_KEY": "fake", "OPENAI_BASE_URL": "http://fake", "MODEL": "test-model"}):
    result1 = _classify_headings_with_llm(headings)

print(f"Indices to remove: {result1}")
assert result1 == {0, 4, 5}, f"Expected {{0, 4, 5}}, got {result1}"
print("PASS: correctly parsed LLM response")
print()

# ── Example 2: LLM returns empty array (nothing to remove) ──────────────────
mock_client2 = make_mock_client("[]")

print("=== Example 2: Nothing to remove ===")
with patch("openai.OpenAI", return_value=mock_client2), \
     patch("dotenv.load_dotenv"), \
     patch.dict(os.environ, {"OPENAI_API_KEY": "fake", "OPENAI_BASE_URL": "http://fake", "MODEL": "test-model"}):
    result2 = _classify_headings_with_llm(["# Results", "# Methods"])

print(f"Indices to remove: {result2}")
assert result2 == set(), f"Expected empty set, got {result2}"
print("PASS: empty array handled correctly")
print()

# ── Example 3: LLM returns unparseable response ─────────────────────────────
mock_client3 = make_mock_client("I'm not sure which ones to remove.")

print("=== Example 3: Unparseable LLM response ===")
with patch("openai.OpenAI", return_value=mock_client3), \
     patch("dotenv.load_dotenv"), \
     patch.dict(os.environ, {"OPENAI_API_KEY": "fake", "OPENAI_BASE_URL": "http://fake", "MODEL": "test-model"}):
    result3 = _classify_headings_with_llm(["# Results"])

print(f"Result: {result3}")
assert result3 is None, f"Expected None, got {result3}"
print("PASS: returns None on unparseable response")
print()

# ── Example 4: API call fails with exception ────────────────────────────────
mock_client4 = make_mock_client(side_effect=Exception("Connection timeout"))

print("=== Example 4: API failure ===")
with patch("openai.OpenAI", return_value=mock_client4), \
     patch("dotenv.load_dotenv"), \
     patch.dict(os.environ, {"OPENAI_API_KEY": "fake", "OPENAI_BASE_URL": "http://fake", "MODEL": "test-model"}):
    result4 = _classify_headings_with_llm(["# Introduction", "# Results"])

print(f"Result: {result4}")
assert result4 is None, f"Expected None on exception, got {result4}"
print("PASS: returns None on API exception")
