"""
example_14_call_extract_api.py

Demonstrates: _call_extract_api(api_client, model, content, name,
                                extract_all_schema, tracker)

Purpose:
    This is the core single-step extraction function. It:
      1. Loads the prompt template
      2. Builds messages: system (prompt) + user (paper content)
      3. Makes ONE API call with the extract_all_genes tool schema
      4. Parses the tool call response (with JSON repair if needed)
      5. Calls _handle_extract_all to get (extraction, gene_dict)
      6. Returns (extraction, gene_dict, success_bool)

    This function is NOT runnable without an actual API key and model.
    Instead, this example walks through the logic with mock objects,
    showing exactly what happens at each step.

    Key design decisions:
      - Uses tool_choice to FORCE the model to call extract_all_genes
      - Records token usage via TokenTracker
      - Returns (None, None, False) on any failure
      - Prints gene counts for monitoring
"""

import json


# ── Step-by-step walkthrough of what _call_extract_api does ──────────────

print("=== Walkthrough: _call_extract_api ===\n")

# Step 1: Build messages
print("Step 1: Build messages")
system_prompt = "(loaded from PROMPT_PATH - detailed extraction instructions)"
paper_content = "# SlMYB12 regulates flavonol biosynthesis\n\n## Results\n..."
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": f"Analyze this literature...\n\nPaper content:\n\n{paper_content}"},
]
print(f"  System message: {len(system_prompt)} chars")
print(f"  User message: {len(messages[1]['content'])} chars")

# Step 2: API call with tool_choice forcing extract_all_genes
print("\nStep 2: API call")
print("  model='claude-sonnet-4-20250514'")
print("  tools=[extract_all_schema]")
print("  tool_choice={'type': 'function', 'function': {'name': 'extract_all_genes'}}")
print("  temperature=0.7, max_tokens=16384")

# Step 3: Parse tool call response
print("\nStep 3: Parse response")
# Simulate what the API returns in the tool call
simulated_arguments = json.dumps({
    "Title": "SlMYB12 regulates flavonol biosynthesis in tomato fruit",
    "Journal": "Molecular Plant",
    "DOI": "10.1016/j.molp.2016.01.001",
    "Common_Genes": [],
    "Pathway_Genes": [
        {"Gene_Name": "CHS", "Enzyme_Name": "Chalcone synthase"},
        {"Gene_Name": "FLS", "Enzyme_Name": "Flavonol synthase"},
    ],
    "Regulation_Genes": [
        {"Gene_Name": "SlMYB12", "Regulation_Type": "MYB transcription factor"},
    ]
})
print(f"  Tool call arguments ({len(simulated_arguments)} chars)")

# Step 4: _safe_parse_json then _handle_extract_all
parsed = json.loads(simulated_arguments)

extraction = {
    "Title": parsed["Title"],
    "Journal": parsed["Journal"],
    "DOI": parsed["DOI"],
    "Common_Genes": parsed["Common_Genes"],
    "Pathway_Genes": parsed["Pathway_Genes"],
    "Regulation_Genes": parsed["Regulation_Genes"],
}

gene_dict = {}
for arr_key, cat in [("Common_Genes", "Common"), ("Pathway_Genes", "Pathway"), ("Regulation_Genes", "Regulation")]:
    for g in parsed.get(arr_key, []):
        gname = g.get("Gene_Name", "")
        if gname:
            gene_dict[gname] = cat

# Step 5: Print results
c = len(extraction["Common_Genes"])
p = len(extraction["Pathway_Genes"])
r = len(extraction["Regulation_Genes"])
total = c + p + r

print(f"\nStep 4: Results")
print(f"  Genes: Common={c}, Pathway={p}, Regulation={r}, Total={total}")
print(f"  gene_dict: {json.dumps(gene_dict, indent=4)}")
print(f"  success: {total > 0}")

# Step 6: Return value
print(f"\nReturn value: (extraction, gene_dict, True)")
print(f"  extraction keys: {list(extraction.keys())}")
print(f"  extraction['Title']: '{extraction['Title']}'")

print("""
NOTE: This example cannot actually call the API.
In production, the function:
  - Catches API exceptions and returns (None, None, False)
  - Uses _safe_parse_json for truncation repair
  - Records tokens via tracker.add(response, stage="extract", file=name)
""")
