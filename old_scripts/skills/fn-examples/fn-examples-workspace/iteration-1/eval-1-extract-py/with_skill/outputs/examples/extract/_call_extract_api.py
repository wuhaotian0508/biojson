"""
_call_extract_api — Single-step API extraction using the extract_all_genes tool.

Makes one OpenAI-compatible API call with function calling to extract paper metadata
and all gene information at once. Returns (extraction_dict, gene_dict, success).

This example uses a mock API client to demonstrate the function without making
real API calls.

Source: extractor/extract.py:349

Usage:
    python _call_extract_api.py
"""

import json
import os
import tempfile
import threading
from datetime import datetime
from typing import Optional, Tuple

# --- Inlined Dependencies ---

# (Inlined from extractor/extract.py:292)
def _safe_parse_json(json_str: str, label: str = "") -> Optional[dict]:
    """Parse JSON with truncation repair."""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass
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

# (Inlined from extractor/extract.py:189)
def _handle_extract_all(arguments: dict) -> Tuple[dict, dict]:
    """Process extract_all_genes result -> (extraction_dict, gene_dict)."""
    extraction = {
        "Title": arguments.get("Title", "NA"),
        "Journal": arguments.get("Journal", "NA"),
        "DOI": arguments.get("DOI", "NA"),
        "Common_Genes": [],
        "Pathway_Genes": [],
        "Regulation_Genes": [],
    }
    gene_dict = {}
    for arr_key, cat in [("Common_Genes", "Common"), ("Pathway_Genes", "Pathway"), ("Regulation_Genes", "Regulation")]:
        genes_arr = arguments.get(arr_key, [])
        if isinstance(genes_arr, str):
            try:
                genes_arr = json.loads(genes_arr)
            except json.JSONDecodeError:
                genes_arr = []
        if not isinstance(genes_arr, list):
            genes_arr = []
        extraction[arr_key] = genes_arr
        for g in genes_arr:
            if isinstance(g, dict):
                gname = g.get("Gene_Name") or g.get("gene") or g.get("gene_name") or g.get("name") or ""
                if gname:
                    gene_dict[gname] = cat
    return extraction, gene_dict

# Minimal TokenTracker (inlined from extractor/token_tracker.py)
class TokenTracker:
    """Minimal token tracker for demonstration."""
    def __init__(self, model="unknown"):
        self.model = model
        self.calls = []
        self._lock = threading.Lock()

    def add(self, response, stage="unknown", file=""):
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

# --- Mock API Client ---
# Simulates an OpenAI-compatible API response with tool calls.

class MockUsage:
    def __init__(self):
        self.prompt_tokens = 4500
        self.completion_tokens = 1200
        self.total_tokens = 5700

class MockFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments

class MockToolCall:
    def __init__(self, function_name, arguments_json):
        self.id = "call_mock_abc123"
        self.function = MockFunction(function_name, arguments_json)

class MockMessage:
    def __init__(self, tool_calls=None):
        self.content = None
        self.tool_calls = tool_calls

class MockChoice:
    def __init__(self, message):
        self.message = message

class MockResponse:
    def __init__(self, message):
        self.choices = [MockChoice(message)]
        self.usage = MockUsage()

class MockCompletions:
    """Mock completions.create() that returns a realistic extract_all_genes response."""
    def create(self, **kwargs):
        # Simulate the LLM returning a tool call with extracted gene data
        tool_result = {
            "Title": "Overexpression of petunia chalcone isomerase in tomato results in fruit containing increased levels of flavonols",
            "Journal": "Nature Biotechnology",
            "DOI": "10.1038/nbt0901-470",
            "Common_Genes": [],
            "Pathway_Genes": [
                {
                    "Gene_Name": "PhCHI",
                    "Species": "tomato (Solanum lycopersicum)",
                    "Pathway": "flavonoid biosynthesis",
                    "Target_Nutrient": "flavonols (quercetin rutinoside, kaempferol rutinoside)",
                    "Phenotype_Direction": "increase (up to 78-fold in fruit peel)",
                },
            ],
            "Regulation_Genes": [],
        }
        arguments_json = json.dumps(tool_result)
        message = MockMessage(
            tool_calls=[MockToolCall("extract_all_genes", arguments_json)]
        )
        return MockResponse(message)

class MockChat:
    def __init__(self):
        self.completions = MockCompletions()

class MockClient:
    """Mock OpenAI client."""
    def __init__(self):
        self.chat = MockChat()

# --- Target Function ---
# Adapted: _load_prompt is replaced with an inline prompt string,
# TEMPERATURE is set as a local constant.

TEMPERATURE = 0.7

def _call_extract_api(
    api_client,
    model: str,
    content: str,
    name: str,
    extract_all_schema: dict,
    tracker,
):
    """Single-step API extraction using extract_all_genes.

    Returns (extraction_dict, gene_dict, success).
    """
    api_kwargs = dict(temperature=TEMPERATURE, max_tokens=16384)
    # In real code, this calls _load_prompt(). Here we use a short stub.
    base_prompt = "You are a plant biology expert. Extract all core genes from the paper."

    user_parts = [
        "Analyze this literature and extract all nutrient metabolism gene information.\n",
        "Extract the paper metadata (Title, Journal, DOI) and ALL core genes at once,",
        "classified into Common_Genes, Pathway_Genes, and Regulation_Genes arrays.\n",
        f"Paper content:\n\n{content}",
    ]

    messages = [
        {"role": "system", "content": base_prompt},
        {"role": "user", "content": "\n".join(user_parts)},
    ]

    print(f"    API Call: extract_all_genes ({model})...")

    try:
        response = api_client.chat.completions.create(
            model=model,
            messages=messages,
            tools=[extract_all_schema],
            tool_choice={"type": "function", "function": {"name": "extract_all_genes"}},
            **api_kwargs,
        )
    except Exception as e:
        print(f"    [{model}] API error (extract_all): {e}")
        return None, None, False

    tracker.add(response, stage="extract", file=name)
    msg = response.choices[0].message

    if not msg.tool_calls:
        print(f"    [{model}] extract_all did not trigger tool call")
        return None, None, False

    tc = msg.tool_calls[0]
    parsed = _safe_parse_json(tc.function.arguments, "extract_all")
    if parsed is None:
        print(f"    extract_all_genes JSON parse failed")
        return None, None, False

    extraction, gene_dict = _handle_extract_all(parsed)

    c = len(extraction.get("Common_Genes", []))
    p = len(extraction.get("Pathway_Genes", []))
    r = len(extraction.get("Regulation_Genes", []))
    total = c + p + r

    print(f"    Genes: Common={c}, Pathway={p}, Regulation={r}, Total={total}")
    print(f"    gene_dict: {gene_dict}")

    if total == 0:
        print(f"    All gene arrays empty")
        return extraction, {}, False

    return extraction, gene_dict, True

# --- Sample Input ---
# Simulates calling the extraction API with a short paper about flavonoid biosynthesis.

paper_content = """\
# Overexpression of petunia chalcone isomerase in tomato results in fruit containing increased levels of flavonols

## Results

We introduced the Petunia hybrida chalcone isomerase gene (PhCHI) into the cultivated tomato
Solanum lycopersicum cv. FM6203 under the control of the CaMV 35S promoter. Transgenic fruit
showed a dramatic increase in flavonol levels. Quercetin rutinoside levels were elevated up to
78-fold in the fruit peel of primary transformants compared with controls. Kaempferol rutinoside
was also significantly increased.

HPLC analysis confirmed that PhCHI expression resulted in the efficient conversion of naringenin
chalcone to naringenin, relieving the rate-limiting step in the flavonoid pathway.
"""

extract_all_schema = {
    "type": "function",
    "function": {
        "name": "extract_all_genes",
        "description": "Extract paper metadata and ALL core genes.",
        "parameters": {
            "type": "object",
            "properties": {
                "Title": {"type": "string"},
                "Journal": {"type": "string"},
                "DOI": {"type": "string"},
                "Common_Genes": {"type": "array", "items": {"type": "object"}},
                "Pathway_Genes": {"type": "array", "items": {"type": "object"}},
                "Regulation_Genes": {"type": "array", "items": {"type": "object"}},
            },
            "required": ["Title", "Journal", "DOI"],
        },
    },
}

# --- Run ---
if __name__ == "__main__":
    mock_client = MockClient()
    tracker = TokenTracker(model="mock-model")

    extraction, gene_dict, success = _call_extract_api(
        api_client=mock_client,
        model="mock-model",
        content=paper_content,
        name="Nat_Biotechnol_2001_Muir.md",
        extract_all_schema=extract_all_schema,
        tracker=tracker,
    )

    print(f"\n=== Success: {success} ===")
    print("\n=== Extraction ===")
    print(json.dumps(extraction, indent=2, ensure_ascii=False))
    print("\n=== Gene Dict ===")
    print(json.dumps(gene_dict, indent=2, ensure_ascii=False))
    print(f"\n=== Token Tracker calls recorded: {len(tracker.calls)} ===")
