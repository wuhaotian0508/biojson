"""
_handle_classify — Process classify_genes function-call result into an extraction
init dict and a gene_dict mapping gene names to normalized categories.

Handles category normalization via CATEGORY_MAP (e.g., "Enzymatic / Biosynthesis"
-> "Pathway", "Transcription factor / Regulatory" -> "Regulation").

Source: extractor/extract.py:246

Usage:
    python _handle_classify.py
"""

import json
from typing import Tuple

# --- Inlined Dependencies ---
# (Inlined from extractor/extract.py:222-243 — category normalization maps)

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

# --- Target Function ---

def _handle_classify(arguments: dict) -> Tuple[dict, dict]:
    """Process classify_genes result -> (extraction_init, gene_dict)."""
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

# --- Sample Input ---
# Simulates the LLM's classify_genes tool call result for a paper about
# anthocyanin engineering in tomato fruit.
arguments = {
    "Title": "Enrichment of tomato fruit with health-promoting anthocyanins by expression of select transcription factors",
    "Journal": "Nature Biotechnology",
    "DOI": "10.1038/nbt1506",
    "genes": [
        {
            "Gene_Name": "Del",
            "category": "Transcription factor / Regulatory",
            "reason": "Snapdragon transcription factor that activates anthocyanin pathway",
        },
        {
            "Gene_Name": "Ros1",
            "category": "Transcription Factor / Regulatory",
            "reason": "MYB transcription factor co-expressed with Del",
        },
        {
            "Gene_Name": "SlDFR",
            "category": "Enzymatic / Biosynthesis",
            "reason": "Dihydroflavonol reductase enzyme in anthocyanin biosynthesis",
        },
        {
            "Gene_Name": "SlANS",
            "category": "biosynthesis",
            "reason": "Anthocyanidin synthase, converts leucoanthocyanidins to anthocyanidins",
        },
        {
            "Gene_Name": "SlGST",
            "category": "Common",
            "reason": "Glutathione S-transferase for anthocyanin transport",
        },
        {
            "Gene_Name": "UNKNOWN_CATEGORY_GENE",
            "category": "SomethingWeird",
            "reason": "Will be normalized to Common as fallback",
        },
    ],
}

# --- Run ---
if __name__ == "__main__":
    extraction, gene_dict = _handle_classify(arguments)

    print("=== Extraction Init ===")
    print(json.dumps(extraction, indent=2, ensure_ascii=False))

    print("\n=== Gene Dict (name -> normalized category) ===")
    print(json.dumps(gene_dict, indent=2, ensure_ascii=False))
