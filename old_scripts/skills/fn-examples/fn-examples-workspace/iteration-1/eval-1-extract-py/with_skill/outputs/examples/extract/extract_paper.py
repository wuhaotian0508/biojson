"""
extract_paper — Extract gene information from a single paper markdown file.

This is the main public API entry point. It reads a markdown file, preprocesses it,
calls the LLM API to extract genes, and saves results to the reports directory.
Supports incremental processing (skips already-extracted papers).

This example uses mocks for the API client, config paths, and text_utils to
demonstrate the function without external dependencies.

Source: extractor/extract.py:426

Usage:
    python extract_paper.py
"""

import json
import os
import tempfile
import threading
from datetime import datetime
from pathlib import Path
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
        return json.loads(repair)
    except json.JSONDecodeError:
        return None

# (Inlined from extractor/extract.py:189)
def _handle_extract_all(arguments: dict) -> Tuple[dict, dict]:
    """Process extract_all_genes result."""
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

# (Inlined from extractor/extract.py:36)
def _schema_props_to_fc(gene_def: dict) -> dict:
    fc_props = {}
    for field_name, field_schema in gene_def.get("properties", {}).items():
        desc = field_schema.get("description", "")
        fc_props[field_name] = {"type": "string", "description": desc}
    return fc_props

# (Inlined from extractor/extract.py:136)
def _build_extract_all_schema(schema_data: dict) -> dict:
    multi = schema_data.get("MultipleGeneExtraction", {})
    defs = multi.get("$defs", {})
    common_props = _schema_props_to_fc(defs.get("CommonGene", {}))
    pathway_props = _schema_props_to_fc(defs.get("PathwayGene", {}))
    regulation_props = _schema_props_to_fc(defs.get("RegulationGene", {}))
    return {
        "type": "function",
        "function": {
            "name": "extract_all_genes",
            "parameters": {
                "type": "object",
                "properties": {
                    "Title": {"type": "string"},
                    "Journal": {"type": "string"},
                    "DOI": {"type": "string"},
                    "Common_Genes": {"type": "array", "items": {"type": "object", "properties": common_props}},
                    "Pathway_Genes": {"type": "array", "items": {"type": "object", "properties": pathway_props}},
                    "Regulation_Genes": {"type": "array", "items": {"type": "object", "properties": regulation_props}},
                },
                "required": ["Title", "Journal", "DOI", "Common_Genes", "Pathway_Genes", "Regulation_Genes"],
            },
        },
    }

# (Inlined from extractor/extract.py:337)
def stem_to_dirname(stem: str) -> str:
    if stem.startswith("MinerU_markdown_"):
        stem = stem[len("MinerU_markdown_"):]
    stem = stem.replace("_(1)", "")
    stem = stem.replace("_", "-")
    return stem

# Minimal TokenTracker
class TokenTracker:
    def __init__(self, model="unknown"):
        self.model = model
        self.calls = []
        self._lock = threading.Lock()
    def add(self, response, stage="unknown", file=""):
        usage = getattr(response, "usage", None)
        if usage is None:
            return
        with self._lock:
            self.calls.append({
                "stage": stage, "file": file,
                "prompt_tokens": usage.prompt_tokens or 0,
                "completion_tokens": usage.completion_tokens or 0,
                "total_tokens": usage.total_tokens or 0,
            })

# Simple preprocess_md stub (strips images and extra blanks)
import re
def preprocess_md(content):
    content = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content

# --- Mock API infrastructure ---

class MockUsage:
    def __init__(self):
        self.prompt_tokens = 3000
        self.completion_tokens = 800
        self.total_tokens = 3800

class MockFn:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments

class MockTC:
    def __init__(self, fn_name, args_json):
        self.id = "call_mock_001"
        self.function = MockFn(fn_name, args_json)

class MockMsg:
    def __init__(self, tool_calls=None):
        self.content = None
        self.tool_calls = tool_calls

class MockChoice:
    def __init__(self, msg):
        self.message = msg

class MockResp:
    def __init__(self, msg):
        self.choices = [MockChoice(msg)]
        self.usage = MockUsage()

class MockCompletions:
    def create(self, **kwargs):
        result = {
            "Title": "Carotenoid biosynthesis in tomato",
            "Journal": "Molecular Plant",
            "DOI": "10.1016/j.molp.2016.05.002",
            "Common_Genes": [],
            "Pathway_Genes": [
                {"Gene_Name": "SlPSY1", "Species": "tomato", "Pathway": "carotenoid biosynthesis"},
                {"Gene_Name": "SlCRTISO", "Species": "tomato", "Pathway": "carotenoid biosynthesis"},
            ],
            "Regulation_Genes": [
                {"Gene_Name": "SlRIN", "Species": "tomato", "Pathway": "ripening regulation"},
            ],
        }
        msg = MockMsg(tool_calls=[MockTC("extract_all_genes", json.dumps(result))])
        return MockResp(msg)

class MockChat:
    def __init__(self):
        self.completions = MockCompletions()

class MockClient:
    def __init__(self):
        self.chat = MockChat()

# --- Target Function ---
# Adapted: replaces config imports with local variables, uses mock clients.

TEMPERATURE = 0.7

def _call_extract_api(api_client, model, content, name, extract_all_schema, tracker):
    """(Inlined from extractor/extract.py:349)"""
    api_kwargs = dict(temperature=TEMPERATURE, max_tokens=16384)
    base_prompt = "You are a plant biology expert. Extract all core genes."
    user_parts = [
        "Analyze this literature and extract all nutrient metabolism gene information.\n",
        f"Paper content:\n\n{content}",
    ]
    messages = [
        {"role": "system", "content": base_prompt},
        {"role": "user", "content": "\n".join(user_parts)},
    ]
    print(f"    API Call: extract_all_genes ({model})...")
    try:
        response = api_client.chat.completions.create(
            model=model, messages=messages,
            tools=[extract_all_schema],
            tool_choice={"type": "function", "function": {"name": "extract_all_genes"}},
            **api_kwargs,
        )
    except Exception as e:
        print(f"    [{model}] API error: {e}")
        return None, None, False

    tracker.add(response, stage="extract", file=name)
    msg = response.choices[0].message
    if not msg.tool_calls:
        return None, None, False

    tc = msg.tool_calls[0]
    parsed = _safe_parse_json(tc.function.arguments, "extract_all")
    if parsed is None:
        return None, None, False

    extraction, gene_dict = _handle_extract_all(parsed)
    c = len(extraction.get("Common_Genes", []))
    p = len(extraction.get("Pathway_Genes", []))
    r = len(extraction.get("Regulation_Genes", []))
    total = c + p + r
    print(f"    Genes: Common={c}, Pathway={p}, Regulation={r}, Total={total}")
    if total == 0:
        return extraction, {}, False
    return extraction, gene_dict, True


def extract_paper(
    md_path,
    tracker,
    reports_dir,
    schema_path,
    get_client_fn,
    get_fallback_fn,
    model="mock-model",
    fallback_model="",
) -> Tuple[Optional[dict], Optional[dict]]:
    """Extract gene information from a single paper.

    (Adapted from extractor/extract.py:426 — config imports replaced with parameters)

    Args:
        md_path: path to the markdown file
        tracker: TokenTracker instance
        reports_dir: directory for reports output
        schema_path: path to schema JSON file
        get_client_fn: callable that returns the primary API client
        get_fallback_fn: callable that returns the fallback API client (or None)
        model: primary model name
        fallback_model: fallback model name

    Returns:
        (extraction_dict, gene_dict) or (None, None) on failure
    """
    md_path = Path(md_path)
    name = md_path.name
    filename = md_path.stem

    # Incremental: skip if already extracted
    paper_dir = Path(reports_dir) / stem_to_dirname(filename)
    output_path = paper_dir / "extraction.json"
    if output_path.exists() and os.getenv("FORCE_RERUN") != "1":
        print(f"  Already exists, skip: {output_path}")
        with open(output_path, "r", encoding="utf-8") as f:
            extraction = json.load(f)
        gene_dict_path = paper_dir / "gene_dict.json"
        if gene_dict_path.exists():
            with open(gene_dict_path, "r", encoding="utf-8") as f:
                gene_dict = json.load(f)
        else:
            gene_dict = {}
            for arr_key, cat in [("Common_Genes", "Common"), ("Pathway_Genes", "Pathway"), ("Regulation_Genes", "Regulation")]:
                for g in extraction.get(arr_key, []):
                    if isinstance(g, dict) and g.get("Gene_Name"):
                        gene_dict[g["Gene_Name"]] = cat
        return extraction, gene_dict

    # Read and preprocess
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_len = len(content)
    content = preprocess_md(content)
    print(f"  Preprocessing: {original_len:,} -> {len(content):,} chars (saved {original_len - len(content):,})")

    # Load schema
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_data = json.load(f)
    extract_all_schema = _build_extract_all_schema(schema_data)

    # Try primary API
    client = get_client_fn()
    fallback_client = get_fallback_fn()

    print(f"  Using primary API ({model})...")
    extraction, gene_dict, success = _call_extract_api(
        client, model, content, name, extract_all_schema, tracker,
    )

    # Fallback
    if not success and fallback_client and fallback_model:
        print(f"  Primary failed, switching to Fallback ({fallback_model})...")
        extraction, gene_dict, success = _call_extract_api(
            fallback_client, fallback_model, content, name, extract_all_schema, tracker,
        )

    if not success or extraction is None:
        print(f"  All APIs failed: {name}")
        paper_dir.mkdir(parents=True, exist_ok=True)
        error_report = {"file": name, "error": "All APIs failed", "timestamp": datetime.now().isoformat()}
        with open(paper_dir / "extraction-error.json", "w", encoding="utf-8") as f:
            json.dump(error_report, f, indent=2, ensure_ascii=False)
        return None, None

    # Save results
    paper_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(extraction, f, indent=2, ensure_ascii=False)
    print(f"  Extraction saved: {output_path}")

    if gene_dict:
        with open(paper_dir / "gene_dict.json", "w", encoding="utf-8") as f:
            json.dump(gene_dict, f, indent=2, ensure_ascii=False)

    return extraction, gene_dict


# --- Sample Input ---
# Create a temporary workspace with a markdown file and schema file.

sample_paper_md = """\
# Carotenoid biosynthesis in ripening tomato fruit

![Figure 1](images/fig1.png)

## Results

The phytoene synthase gene SlPSY1 was found to be the rate-limiting enzyme in carotenoid
biosynthesis during tomato fruit ripening. Overexpression of SlPSY1 in transgenic tomato lines
led to a 2.5-fold increase in total carotenoid content compared to wild-type controls.

The carotenoid isomerase SlCRTISO was required for the conversion of prolycopene to
all-trans-lycopene. CRISPR knockout of SlCRTISO resulted in yellow-fleshed fruit with
significantly reduced lycopene levels.

The MADS-box transcription factor SlRIN (RIPENING INHIBITOR) directly binds to the promoter
of SlPSY1 and activates its expression during fruit ripening.

## Methods

Transgenic tomato plants were generated using Agrobacterium-mediated transformation.
Carotenoid levels were quantified by HPLC analysis.

## References

1. Liu et al. (2015) Plant Cell 27:2846-2859.
2. Fray & Grierson (1993) Plant Mol Biol 22:589-602.
"""

sample_schema = {
    "MultipleGeneExtraction": {
        "$defs": {
            "CommonGene": {
                "properties": {
                    "Gene_Name": {"description": "Gene name or symbol."},
                    "Species": {"description": "Main species."},
                }
            },
            "PathwayGene": {
                "properties": {
                    "Gene_Name": {"description": "Gene name or symbol."},
                    "Pathway": {"description": "Metabolic pathway."},
                }
            },
            "RegulationGene": {
                "properties": {
                    "Gene_Name": {"description": "Gene name or symbol."},
                    "Pathway": {"description": "Regulatory pathway."},
                }
            },
        }
    }
}

# --- Run ---
if __name__ == "__main__":
    # Set up temp workspace
    tmpdir = tempfile.mkdtemp(prefix="extract_paper_demo_")
    md_path = os.path.join(tmpdir, "Mol_Plant_2016_Yang.md")
    schema_path = os.path.join(tmpdir, "schema.json")
    reports_dir = os.path.join(tmpdir, "reports")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(sample_paper_md)
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(sample_schema, f, indent=2)

    tracker = TokenTracker(model="mock-model")

    extraction, gene_dict = extract_paper(
        md_path=md_path,
        tracker=tracker,
        reports_dir=reports_dir,
        schema_path=schema_path,
        get_client_fn=lambda: MockClient(),
        get_fallback_fn=lambda: None,
        model="mock-model",
        fallback_model="",
    )

    print("\n=== Final Extraction ===")
    print(json.dumps(extraction, indent=2, ensure_ascii=False))
    print("\n=== Gene Dict ===")
    print(json.dumps(gene_dict, indent=2, ensure_ascii=False))

    # Verify saved files
    paper_dir = os.path.join(reports_dir, stem_to_dirname("Mol_Plant_2016_Yang"))
    print(f"\n=== Saved files in {paper_dir} ===")
    if os.path.isdir(paper_dir):
        for fname in os.listdir(paper_dir):
            fpath = os.path.join(paper_dir, fname)
            print(f"  {fname} ({os.path.getsize(fpath)} bytes)")

    # Cleanup
    import shutil
    shutil.rmtree(tmpdir)
    print(f"\n(Temp directory cleaned up)")
