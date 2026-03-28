"""
_load_prompt — Load the extraction prompt text from the configured prompt file.

In the real pipeline this reads from PROMPT_PATH (nutri_gene_prompt_v4.txt).
This example uses a temporary file to demonstrate the function without
requiring the actual prompt file.

Source: extractor/extract.py:30

Usage:
    python _load_prompt.py
"""

import os
import tempfile

# --- Target Function ---
# Modified to accept a path parameter so it can run standalone with a temp file.
# Original reads from the module-level PROMPT_PATH constant.

def _load_prompt(prompt_path):
    """(Adapted from extractor/extract.py:30 — original uses PROMPT_PATH constant)"""
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

# --- Sample Input ---
# Create a temporary prompt file with a realistic excerpt of the extraction prompt.
sample_prompt_text = """\
# Nutrient Metabolism Gene Extraction Prompt

You are a plant biology expert. Your task is to extract information about core genes
that control the presence, yield, or content of final nutritional products in crops.

## Definition of Core Gene
A "core gene" is one whose experimental perturbation (knockout, overexpression, RNAi,
or natural allelic variation) causes a measurable change in the target nutrient in
the harvested crop tissue.

## Evidence Hierarchy
1. Genetic perturbation (knockout/overexpression with metabolite quantification)
2. Enzyme assay (in vitro or in vivo catalytic activity)
3. Correlation (expression correlated with nutrient level, weakest evidence)

## Output Format
Return a JSON object with Title, Journal, DOI, and three gene arrays:
Common_Genes, Pathway_Genes, Regulation_Genes.
"""

# --- Run ---
if __name__ == "__main__":
    # Write sample prompt to a temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(sample_prompt_text)
        temp_path = f.name

    try:
        result = _load_prompt(temp_path)
        print("=== Loaded Prompt ===")
        print(result[:500])
        print(f"\n... ({len(result)} characters total)")
    finally:
        os.unlink(temp_path)
