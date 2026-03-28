"""
example_15_extract_paper.py

Demonstrates: extract_paper(md_path, tracker)

Purpose:
    This is the PUBLIC API - the main entry point for extracting gene
    information from a single paper. It orchestrates the full pipeline:

    1. Check if extraction already exists (skip if so, unless FORCE_RERUN=1)
    2. Read the markdown file
    3. Preprocess it (strip images, URLs, irrelevant sections)
    4. Load the extract_all_genes schema
    5. Call primary API via _call_extract_api
    6. If primary fails, try fallback API
    7. Save extraction.json and gene_dict.json to reports/<paper-dir>/
    8. Return (extraction_dict, gene_dict) or (None, None) on failure

    This function requires API credentials and actual files, so this
    example walks through the logic with annotations rather than
    running the real function.
"""

import json
import os
from pathlib import Path
from datetime import datetime


print("=== extract_paper() Walkthrough ===\n")

# ── Step 1: Incremental check ────────────────────────────────────────────

print("Step 1: Incremental check")
md_path = Path("md/Mol_Plant_2016_Yang.md")
stem = md_path.stem  # "Mol_Plant_2016_Yang"

# stem_to_dirname converts it for report directory
def stem_to_dirname(s):
    if s.startswith("MinerU_markdown_"):
        s = s[len("MinerU_markdown_"):]
    s = s.replace("_(1)", "")
    s = s.replace("_", "-")
    return s

dirname = stem_to_dirname(stem)  # "Mol-Plant-2016-Yang"
print(f"  File stem: {stem}")
print(f"  Report dir: reports/{dirname}/")
print(f"  Output path: reports/{dirname}/extraction.json")

# Check if already exists
output_exists = False  # simulated
print(f"  Already extracted: {output_exists}")
if output_exists:
    print("  -> Would skip and load existing extraction.json + gene_dict.json")
    print("  -> Set FORCE_RERUN=1 to re-extract")

# ── Step 2: Read and preprocess ──────────────────────────────────────────

print("\nStep 2: Read and preprocess markdown")
# In real code: content = open(md_path).read() then preprocess_md(content)
original_len = 45000
processed_len = 28000
saved = original_len - processed_len
print(f"  Original: {original_len:,} chars")
print(f"  After preprocessing: {processed_len:,} chars")
print(f"  Saved: {saved:,} chars ({saved*100//original_len}% reduction)")
print("  (strips images, URLs, references, acknowledgments, introduction)")

# ── Step 3: API extraction ────────────────────────────���──────────────────

print("\nStep 3: Primary API extraction")
print("  Model: claude-sonnet-4-20250514 (from config.MODEL)")
print("  -> Calls _call_extract_api with extract_all_genes tool")

# Simulate success
success = True
extraction = {
    "Title": "The R2R3-MYB transcription factor MYB12 controls flavonol biosynthesis",
    "Journal": "Molecular Plant",
    "DOI": "10.1016/j.molp.2016.01.001",
    "Common_Genes": [],
    "Pathway_Genes": [
        {"Gene_Name": "CHS", "Enzyme_Name": "Chalcone synthase"},
        {"Gene_Name": "F3H", "Enzyme_Name": "Flavanone 3-hydroxylase"},
    ],
    "Regulation_Genes": [
        {"Gene_Name": "SlMYB12", "Regulation_Type": "MYB transcription factor"},
    ],
}
gene_dict = {"CHS": "Pathway", "F3H": "Pathway", "SlMYB12": "Regulation"}

if not success:
    print("\nStep 3b: Fallback API")
    print("  Model: (from config.FALLBACK_MODEL)")
    print("  -> Retries with fallback client")

# ── Step 4: Save results ─────────────────────────────────────────────────

print(f"\nStep 4: Save results")
print(f"  reports/{dirname}/extraction.json  (full extraction with gene arrays)")
print(f"  reports/{dirname}/gene_dict.json   (gene name -> category mapping)")

print(f"\nExtraction result:")
print(f"  Title: {extraction['Title']}")
print(f"  Common: {len(extraction['Common_Genes'])} genes")
print(f"  Pathway: {len(extraction['Pathway_Genes'])} genes")
print(f"  Regulation: {len(extraction['Regulation_Genes'])} genes")
print(f"\ngene_dict: {json.dumps(gene_dict, indent=2)}")

# ── Step 5: Return ──────────────────────────────────────────────────────

print(f"\nReturn: (extraction, gene_dict)")
print(f"  On failure: (None, None)")

# ── Failure case ─────────────────────────────────────────────────────────

print("\n--- Failure case ---")
print("If both primary and fallback APIs fail:")
print(f"  Saves: reports/{dirname}/extraction-error.json")
error_report = {
    "file": "Mol_Plant_2016_Yang.md",
    "error": "All APIs failed",
    "timestamp": datetime.now().isoformat(),
}
print(f"  Error report: {json.dumps(error_report, indent=2)}")
print(f"  Returns: (None, None)")
