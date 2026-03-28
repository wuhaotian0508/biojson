"""
extract.py — Gene extraction with inline function calling.

Single-step API call:
    extract_all_genes → Title/Journal/DOI + Common_Genes/Pathway_Genes/Regulation_Genes

Function calling schemas are built directly from the schema JSON file.
"""

import json
import os
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Optional, Tuple

from .config import (
    MODEL, TEMPERATURE, FALLBACK_MODEL,
    PROMPT_PATH, SCHEMA_PATH, REPORTS_DIR,
    get_openai_client, get_fallback_client,
)
from .text_utils import preprocess_md_for_llm
from .token_tracker import TokenTracker
from .utils import (
    GENE_ARRAY_KEYS, ensure_list, get_gene_name,
    safe_parse_json, stem_to_dirname,
)


# ─── Load prompt (cached) ───────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_prompt():
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


# ─── Build FC schemas from schema JSON ──────────────────────────────────────

def _schema_props_to_fc(gene_def: dict) -> dict:
    """Convert a gene type's properties to FC-compatible format."""
    fc_props = {}
    for field_name, field_schema in gene_def.get("properties", {}).items():
        desc = field_schema.get("description", "")
        fc_props[field_name] = {"type": "string", "description": desc}
    return fc_props


def _build_extract_all_schema(schema_data: dict) -> dict:
    """Build the extract_all_genes FC schema from MultipleGeneExtraction."""
    multi = schema_data.get("MultipleGeneExtraction", {})
    defs = multi.get("$defs", {})

    common_props = _schema_props_to_fc(defs.get("CommonGene", {}))
    pathway_props = _schema_props_to_fc(defs.get("PathwayGene", {}))
    regulation_props = _schema_props_to_fc(defs.get("RegulationGene", {}))

    return {
        "type": "function",
        "function": {
            "name": "extract_all_genes",
            "description": (
                "Extract paper metadata and ALL core genes at once, classified into "
                "three arrays: Common_Genes, Pathway_Genes, Regulation_Genes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "Title": {"type": "string", "description": "Full paper title."},
                    "Journal": {"type": "string", "description": "Journal name."},
                    "DOI": {"type": "string", "description": "Pure DOI string, no URL prefix."},
                    "Common_Genes": {
                        "type": "array",
                        "description": "Common genes (general function in nutrient metabolism).",
                        "items": {"type": "object", "properties": common_props},
                    },
                    "Pathway_Genes": {
                        "type": "array",
                        "description": "Pathway genes (biosynthetic/metabolic enzyme genes).",
                        "items": {"type": "object", "properties": pathway_props},
                    },
                    "Regulation_Genes": {
                        "type": "array",
                        "description": "Regulation genes (TFs, signaling, regulators).",
                        "items": {"type": "object", "properties": regulation_props},
                    },
                },
                "required": ["Title", "Journal", "DOI", "Common_Genes", "Pathway_Genes", "Regulation_Genes"],
            },
        },
    }


@lru_cache(maxsize=1)
def _load_extract_all_schema() -> dict:
    """Load the single extract_all_genes schema (cached)."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_data = json.load(f)
    return _build_extract_all_schema(schema_data)


def _handle_extract_all(arguments: dict) -> Tuple[dict, dict]:
    """Process extract_all_genes result → (extraction_dict, gene_dict)."""
    extraction = {
        "Title": arguments.get("Title", "NA"),
        "Journal": arguments.get("Journal", "NA"),
        "DOI": arguments.get("DOI", "NA"),
        "Common_Genes": [],
        "Pathway_Genes": [],
        "Regulation_Genes": [],
    }

    gene_dict = {}
    for arr_key, cat in GENE_ARRAY_KEYS:
        genes_arr = ensure_list(arguments.get(arr_key, []))
        extraction[arr_key] = genes_arr
        for g in genes_arr:
            if isinstance(g, dict):
                gname = get_gene_name(g)
                if gname:
                    gene_dict[gname] = cat

    return extraction, gene_dict


# ═══════════════════════════════════════════════════════════════════════════════
#  Core extraction: single-step API call
# ═══════════════════════════════════════════════════════════════════════════════

def _call_extract_api(
    api_client,
    model: str,
    content: str,
    name: str,
    extract_all_schema: dict,
    tracker: TokenTracker,
):
    """Single-step API extraction using extract_all_genes.

    Returns (extraction_dict, gene_dict, success).
    """
    api_kwargs = dict(temperature=TEMPERATURE, max_tokens=16384)
    base_prompt = _load_prompt()

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

    print(f"    🔵 API Call: extract_all_genes ({model})...")

    try:
        response = api_client.chat.completions.create(
            model=model,
            messages=messages,
            tools=[extract_all_schema],
            tool_choice={"type": "function", "function": {"name": "extract_all_genes"}},
            **api_kwargs,
        )
    except Exception as e:
        print(f"    ❌ [{model}] API error (extract_all): {e}")
        return None, None, False

    tracker.add(response, stage="extract", file=name)
    msg = response.choices[0].message

    if not msg.tool_calls:
        print(f"    ⚠️  [{model}] extract_all did not trigger tool call")
        return None, None, False

    tc = msg.tool_calls[0]
    parsed = safe_parse_json(tc.function.arguments, "extract_all")
    if parsed is None:
        print(f"    ❌ extract_all_genes JSON parse failed")
        return None, None, False

    extraction, gene_dict = _handle_extract_all(parsed)

    c = len(extraction.get("Common_Genes", []))
    p = len(extraction.get("Pathway_Genes", []))
    r = len(extraction.get("Regulation_Genes", []))
    total = c + p + r

    print(f"    📊 Genes: Common={c}, Pathway={p}, Regulation={r}, Total={total}")
    print(f"    📋 gene_dict: {gene_dict}")

    if total == 0:
        print(f"    ⚠️  All gene arrays empty")
        return extraction, {}, False

    return extraction, gene_dict, True


# ═══════════════════════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════════════════════

def extract_paper(
    md_path,
    tracker: TokenTracker,
) -> Tuple[Optional[dict], Optional[dict]]:
    """Extract gene information from a single paper.

    Args:
        md_path: path to the markdown file
        tracker: TokenTracker instance

    Returns:
        (extraction_dict, gene_dict) or (None, None) on failure
    """
    md_path = Path(md_path)
    name = md_path.name
    filename = md_path.stem

    # Incremental: skip if already extracted
    paper_dir = REPORTS_DIR / stem_to_dirname(filename)
    output_path = paper_dir / "extraction.json"
    if output_path.exists() and os.getenv("FORCE_RERUN") != "1":
        print(f"  ⏭️  Already exists, skip: {output_path}  (set FORCE_RERUN=1 to re-run)")
        with open(output_path, "r", encoding="utf-8") as f:
            extraction = json.load(f)
        gene_dict_path = paper_dir / "gene_dict.json"
        if gene_dict_path.exists():
            with open(gene_dict_path, "r", encoding="utf-8") as f:
                gene_dict = json.load(f)
        else:
            gene_dict = {}
            for arr_key, cat in GENE_ARRAY_KEYS:
                for g in extraction.get(arr_key, []):
                    if isinstance(g, dict) and g.get("Gene_Name"):
                        gene_dict[g["Gene_Name"]] = cat
        return extraction, gene_dict

    # Read and preprocess
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_len = len(content)
    content = preprocess_md_for_llm(content, tracker=tracker)
    print(f"  📏 Preprocessing: {original_len:,} → {len(content):,} chars (saved {original_len - len(content):,})")

    # Load schema
    extract_all_schema = _load_extract_all_schema()

    # Try primary API
    client = get_openai_client()
    fallback_client = get_fallback_client()

    print(f"  🔵 Using primary API ({MODEL})...")
    extraction, gene_dict, success = _call_extract_api(
        client, MODEL, content, name, extract_all_schema, tracker,
    )

    # Fallback
    if not success and fallback_client and FALLBACK_MODEL:
        print(f"  🔄 Primary failed, switching to Fallback ({FALLBACK_MODEL})...")
        extraction, gene_dict, success = _call_extract_api(
            fallback_client, FALLBACK_MODEL, content, name, extract_all_schema, tracker,
        )

    if not success or extraction is None:
        print(f"  ⚠️  All APIs failed: {name}")
        paper_dir.mkdir(parents=True, exist_ok=True)
        error_report = {
            "file": name,
            "error": "All APIs failed",
            "timestamp": datetime.now().isoformat(),
        }
        with open(paper_dir / "extraction-error.json", "w", encoding="utf-8") as f:
            json.dump(error_report, f, indent=2, ensure_ascii=False)
        return None, None

    # Save results
    paper_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(extraction, f, indent=2, ensure_ascii=False)
    print(f"  ✅ Extraction saved: {output_path}")

    if gene_dict:
        with open(paper_dir / "gene_dict.json", "w", encoding="utf-8") as f:
            json.dump(gene_dict, f, indent=2, ensure_ascii=False)

    return extraction, gene_dict
