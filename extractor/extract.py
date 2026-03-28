"""
extract.py — Gene extraction with inline function calling.

Replaces: scripts/md_to_json.py + scripts/tool_registry.py + skills/handlers.py

Single-step API call:
    extract_all_genes → Title/Journal/DOI + Common_Genes/Pathway_Genes/Regulation_Genes

Function calling schemas are built directly from the schema JSON file.
Handler logic is inlined as helper functions.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from .config import (
    MODEL, TEMPERATURE, FALLBACK_MODEL,
    PROMPT_PATH, SCHEMA_PATH, REPORTS_DIR,
    get_openai_client, get_fallback_client, ensure_dirs,
)
from .text_utils import preprocess_md
from .token_tracker import TokenTracker


# ─── Load prompt ──────────────────────────────────────────────────────────────
def _load_prompt():
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()

# ─── Build FC schemas from schema JSON ────────────────────────────────────────

def _schema_props_to_fc(gene_def: dict) -> dict:
    """Convert a gene type's properties to FC-compatible format."""
    fc_props = {}
    for field_name, field_schema in gene_def.get("properties", {}).items():
        desc = field_schema.get("description", "")
        fc_props[field_name] = {"type": "string", "description": desc}
    return fc_props


def _build_extract_schema(schema_data: dict, section_key: str, tool_name: str, description: str) -> dict:
    """Build an OpenAI function calling tool schema from a schema section."""
    section = schema_data.get(section_key, {})
    defs = section.get("$defs", {})
    gene_type_name = list(defs.keys())[0] if defs else None
    gene_props = {}
    if gene_type_name:
        gene_props = _schema_props_to_fc(defs[gene_type_name])

    return {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    "genes": {
                        "type": "array",
                        "description": f"Detailed information for each gene.",
                        "items": {"type": "object", "properties": gene_props}
                    }
                },
                "required": ["genes"]
            }
        }
    }


def _build_classify_schema() -> dict:
    """Build the classify_genes FC schema (inline, no file reference)."""
    return {
        "type": "function",
        "function": {
            "name": "classify_genes",
            "description": (
                "Identify ALL core genes from the paper's Results section and classify each into "
                "one of three categories: Common / Pathway / Regulation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "Title": {"type": "string", "description": "Full paper title."},
                    "Journal": {"type": "string", "description": "Journal name."},
                    "DOI": {"type": "string", "description": "Pure DOI string, no URL prefix."},
                    "genes": {
                        "type": "array",
                        "description": "List of all core genes identified from the paper.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "Gene_Name": {"type": "string", "description": "Gene name or symbol."},
                                "category": {
                                    "type": "string",
                                    "enum": ["Common", "Pathway", "Regulation"],
                                    "description": "Gene category.",
                                },
                                "reason": {"type": "string", "description": "Brief reason for classification."},
                            },
                            "required": ["Gene_Name", "category"],
                        },
                    },
                },
                "required": ["Title", "Journal", "DOI", "genes"],
            },
        },
    }


def _load_extract_schemas():
    """Load all extraction tool schemas from schema JSON file (legacy 2-step)."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_data = json.load(f)

    return {
        "classify_genes": _build_classify_schema(),
        "extract_common_genes": _build_extract_schema(
            schema_data, "CommonGeneExtraction", "extract_common_genes",
            "Extract detailed field information for Common genes.",
        ),
        "extract_pathway_genes": _build_extract_schema(
            schema_data, "PathwayGeneExtraction", "extract_pathway_genes",
            "Extract detailed field information for Pathway genes (biosynthetic/metabolic enzyme genes).",
        ),
        "extract_regulation_genes": _build_extract_schema(
            schema_data, "RegulationGeneExtraction", "extract_regulation_genes",
            "Extract detailed field information for Regulation genes (TFs, signaling, regulators).",
        ),
    }


def _build_extract_all_schema(schema_data: dict) -> dict:
    """Build the extract_all_genes FC schema from MultipleGeneExtraction."""
    multi = schema_data.get("MultipleGeneExtraction", {})
    defs = multi.get("$defs", {})

    # Build FC properties for each gene type
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


def _load_extract_all_schema() -> dict:
    """Load the single extract_all_genes schema."""
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


# ─── Inline handler logic ────────────────────────────────────────────────────

CATEGORY_MAP = {
    "Enzymatic / Biosynthesis": "Pathway",
    "Transcription factor / Regulatory": "Regulation",
    "Transcription Factor / Regulatory": "Regulation",
    "enzymatic / biosynthesis": "Pathway",
    "transcription factor / regulatory": "Regulation",
    "Enzymatic": "Pathway",
    "Biosynthesis": "Pathway",
    "Transcription factor": "Regulation",
    "Regulatory": "Regulation",
    "biosynthesis": "Pathway",
    "regulatory": "Regulation",
    "transcription factor": "Regulation",
    "enzyme": "Pathway",
    "Enzyme": "Pathway",
}

CAT_TO_TOOL = {
    "Common":     "extract_common_genes",
    "Pathway":    "extract_pathway_genes",
    "Regulation": "extract_regulation_genes",
}


def _handle_classify(arguments: dict) -> Tuple[dict, dict]:
    """Process classify_genes result → (extraction_init, gene_dict)."""
    extraction = {
        "Title": arguments.get("Title", "NA"),
        "Journal": arguments.get("Journal", "NA"),
        "DOI": arguments.get("DOI", "NA"),
        "Common_Genes": [],
        "Pathway_Genes": [],
        "Regulation_Genes": [],
    }

    genes_list = arguments.get("genes", [])
    if isinstance(genes_list, str):
        try:
            genes_list = json.loads(genes_list)
        except json.JSONDecodeError:
            genes_list = []

    gene_dict = {}
    for g in genes_list:
        if not isinstance(g, dict):
            continue
        gname = g.get("Gene_Name") or g.get("gene") or g.get("gene_name") or g.get("name") or ""
        cat = g.get("category", "Common")
        cat = CATEGORY_MAP.get(cat, cat)
        if cat not in ("Common", "Pathway", "Regulation"):
            cat = "Common"
        if gname:
            gene_dict[gname] = cat

    return extraction, gene_dict


def _handle_extract(arguments: dict, arr_key: str) -> list:
    """Process extract_*_genes result → gene array."""
    genes_arr = arguments.get("genes", [])
    if isinstance(genes_arr, str):
        try:
            genes_arr = json.loads(genes_arr)
        except json.JSONDecodeError:
            genes_arr = []
    return genes_arr if isinstance(genes_arr, list) else []


# ─── JSON repair ──────────────────────────────────────────────────────────────

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
            print(f"    🔧 [{label}] Truncated JSON auto-repaired")
        return result
    except json.JSONDecodeError:
        return None


def _message_to_dict(message) -> dict:
    """Convert an OpenAI message object to dict."""
    msg = {"role": "assistant", "content": message.content or None}
    if message.tool_calls:
        msg["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in message.tool_calls
        ]
    return msg


# ─── Stem → dirname helper ───────────────────────────────────────────────────

def stem_to_dirname(stem: str) -> str:
    if stem.startswith("MinerU_markdown_"):
        stem = stem[len("MinerU_markdown_"):]
    stem = stem.replace("_(1)", "")
    stem = stem.replace("_", "-")
    return stem


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

    # Build user message
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

    # ── Single API Call: extract_all_genes ────────────────────────────────────
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
    parsed = _safe_parse_json(tc.function.arguments, "extract_all")
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
