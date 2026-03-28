"""
example_11_load_prompt.py

Demonstrates: _load_prompt()

Purpose:
    Reads the extraction prompt template from the file specified by
    PROMPT_PATH (configured in config.py). This prompt contains detailed
    instructions telling the AI how to identify and extract "core genes"
    from scientific papers.

    In the real pipeline, PROMPT_PATH points to:
        extractor/prompts/nutri_gene_prompt_v4.txt

    This example shows the function's behavior by simulating it with
    a temporary file, since we don't want to depend on the actual
    prompt file path.
"""

import tempfile
import os


def _load_prompt(prompt_path):
    """Read the prompt template from disk."""
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


# ── Example: simulate loading a prompt file ──────────────────────────────

# Create a temporary prompt file to demonstrate
sample_prompt = """You are a scientific literature analysis expert.

Your task is to extract ALL core genes related to nutrient metabolism
from the provided research paper.

For each gene, determine:
1. Gene_Name: Official gene symbol
2. Species: Where the gene was studied
3. Category: Common / Pathway / Regulation
4. Evidence: Type of experimental validation

Focus on genes with DIRECT experimental evidence of affecting
nutrient content (vitamins, minerals, carotenoids, flavonoids, etc.)

Return results using the extract_all_genes function call.
"""

# Write to a temp file and load it
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
    f.write(sample_prompt)
    temp_path = f.name

prompt = _load_prompt(temp_path)
print(f"Loaded prompt from: {temp_path}")
print(f"Prompt length: {len(prompt)} characters")
print(f"First 200 chars:\n{prompt[:200]}...")

# Clean up
os.unlink(temp_path)

# In the real code, _load_prompt() is called with no arguments and reads
# from the global PROMPT_PATH constant. The loaded prompt becomes the
# system message in the API call.
