"""
_safe_parse_json — Parse a JSON string with automatic repair for truncated output.

When the LLM returns truncated JSON (e.g., due to max_tokens cutoff), this
function attempts to repair the string by balancing braces and brackets.

Source: extractor/extract.py:292

Usage:
    python _safe_parse_json.py
"""

import json
from typing import Optional

# --- Target Function ---

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

# --- Sample Input ---

# Case 1: Valid JSON (no repair needed)
valid_json = '{"Gene_Name": "SlCHI", "Species": "tomato", "Pathway": "flavonoid biosynthesis"}'

# Case 2: Truncated JSON — the LLM ran out of tokens mid-response.
# The closing brackets/braces are missing.
truncated_json = '{"genes": [{"Gene_Name": "SlMYB12", "Species": "tomato"}, {"Gene_Name": "AtPAP1", "Species": "Arabidopsis"'

# Case 3: Completely broken (no braces at all)
broken_json = "This is not JSON at all"

# Case 4: Truncated with nested arrays
nested_truncated = '{"Title": "Flavonoid study", "Common_Genes": [{"Gene_Name": "CHS"}, {"Gene_Name": "CHI"'

# --- Run ---
if __name__ == "__main__":
    print("=== Case 1: Valid JSON ===")
    result1 = _safe_parse_json(valid_json, label="valid")
    print(json.dumps(result1, indent=2, ensure_ascii=False))

    print("\n=== Case 2: Truncated JSON ===")
    result2 = _safe_parse_json(truncated_json, label="truncated")
    print(json.dumps(result2, indent=2, ensure_ascii=False))

    print("\n=== Case 3: Completely broken ===")
    result3 = _safe_parse_json(broken_json, label="broken")
    print(f"Result: {result3}")

    print("\n=== Case 4: Nested truncated ===")
    result4 = _safe_parse_json(nested_truncated, label="nested")
    print(json.dumps(result4, indent=2, ensure_ascii=False))
