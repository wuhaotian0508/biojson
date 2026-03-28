"""
example_08_safe_parse_json.py

Demonstrates: _safe_parse_json(json_str, label)

Purpose:
    Parses a JSON string with automatic repair of truncated JSON.
    This is important because the AI API sometimes returns truncated JSON
    when hitting max_tokens limits.

    Repair strategy:
      1. Try normal json.loads() first
      2. If that fails, find the last '}' in the string
      3. Count unmatched '{' and '[' brackets
      4. Append closing brackets to balance them
      5. Try parsing the repaired string

    Returns the parsed dict on success, or None on failure.
"""

import json
from typing import Optional


def _safe_parse_json(json_str: str, label: str = "") -> Optional[dict]:
    """Parse JSON with truncation repair."""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # Try repair
    last_brace = json_str.rfind('}')
    if last_brace == -1:
        return None

    truncated = json_str[:last_brace + 1]
    ob = truncated.count('{') - truncated.count('}')
    obr = truncated.count('[') - truncated.count(']')
    repair = truncated + ']' * max(0, obr) + '}' * max(0, ob)
    try:
        result = json.loads(repair)
        if label:
            print(f"    [repair] [{label}] Truncated JSON auto-repaired")
        return result
    except json.JSONDecodeError:
        return None


# ── Example 1: Valid JSON (no repair needed) ─────────────────────────────

print("=== Example 1: Valid JSON ===")
valid = '{"Gene_Name": "CHS", "category": "Pathway"}'
result = _safe_parse_json(valid, "test1")
print(f"Input:  {valid}")
print(f"Output: {result}")

# ── Example 2: Truncated JSON (missing closing brackets) ─────────────────

print("\n=== Example 2: Truncated JSON - missing closing brackets ===")
truncated = '{"genes": [{"Gene_Name": "CHS"}, {"Gene_Name": "CHI"'
# The AI was cut off mid-response. The function repairs it.
result = _safe_parse_json(truncated, "truncated_example")
print(f"Input:  {truncated}")
print(f"Output: {result}")
# Note: the second gene is lost because it was incomplete

# ── Example 3: Truncated with nested structure ───────────────────────────

print("\n=== Example 3: Truncated nested structure ===")
nested_truncated = '{"Title": "Test", "Pathway_Genes": [{"Gene_Name": "F3H", "Product": "DHK"}]}'
# This one is actually valid, just checking it works
result = _safe_parse_json(nested_truncated, "nested")
print(f"Parsed: {json.dumps(result, indent=2)}")

# ── Example 4: Missing array bracket ────────────────────────────────────

print("\n=== Example 4: Missing array bracket ===")
missing_bracket = '{"genes": [{"Gene_Name": "CHS"}, {"Gene_Name": "CHI"}}'
# Missing the closing ']' for the array
result = _safe_parse_json(missing_bracket, "missing_bracket")
print(f"Input:  {missing_bracket}")
print(f"Output: {result}")

# ── Example 5: Completely broken (no braces at all) ─────────────────────

print("\n=== Example 5: Completely broken - no braces ===")
broken = "This is not JSON at all"
result = _safe_parse_json(broken, "broken")
print(f"Input:  {broken}")
print(f"Output: {result}")  # None
