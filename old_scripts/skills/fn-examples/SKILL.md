---
name: fn-examples
description: >
  Generate standalone runnable Python example files for every function in a given .py file or folder.
  Each function gets its own directory under examples/ with a self-contained .py file that includes
  sample inputs, the function itself (plus inlined dependencies), and a __main__ block that calls it.
  Use this skill when the user wants to understand what functions do, create quick-reference examples,
  generate function demos, or asks to "write examples for each function", "create runnable demos",
  "make a test file for every function", or "help me understand this code by running each function".
  Also trigger when the user says things like "给每个函数写一个样例" or "帮我理解这些函数".
---

# fn-examples: Standalone Function Example Generator

## What This Skill Does

Given a Python file (or folder of .py files), produce one **standalone, directly runnable** `.py` file per function. The file is named after the function and placed under `examples/<source_filename>/`. It contains everything needed to run in isolation — no external project imports required.

The purpose is rapid comprehension: a developer can open any example, read the sample data, see the function, and run it to immediately understand what the function does.

**Every function must have a corresponding .py file. No exceptions, no skipping.** One function = one file, strict 1:1 mapping.

## Output Structure

For a single file `extract.py`:
```
examples/
└── extract/
    ├── _schema_props_to_fc.py
    ├── _build_extract_schema.py
    ├── _build_classify_schema.py
    ├── _handle_extract_all.py
    ├── stem_to_dirname.py
    ├── extract_paper.py
    └── ...                        ← every function gets a file
```

For a folder with multiple .py files:
```
examples/
├── module_a/
│   ├── func_x.py
│   ├── func_y.py
│   └── _helper_z.py
├── module_b/
│   ├── ClassA_method1.py
│   └── ClassA_method2.py
└── README.md
```

Key rules:
- Directory name = source filename without `.py` extension
- File name = function name + `.py` (e.g., `_schema_props_to_fc.py`)
- For class methods: `ClassName_method_name.py` (e.g., `TokenTracker_add.py`)
- Each `.py` file is independently runnable with `python <name>.py`

## Step-by-Step Process

### 1. Inventory all functions

Read the target file(s) and list **every** function and class method. No exceptions — every function gets its own file.

Include:
- Top-level functions (both public and `_private`)
- Class methods (instance methods, classmethods, staticmethods)
- `__init__` methods
- Nested functions if they are the primary logic carrier
- Even trivial one-liners (they still get a file — the example shows what simple thing they do)

For each function, note:
- **Name** and **signature** (parameters + type hints if any)
- **Docstring** / inline comments describing its purpose
- **Internal dependencies**: other functions from the same file that this function calls
- **External imports**: third-party or stdlib imports the function needs

### 2. Resolve dependency chains

For each function, walk its call graph within the same file. If `func_A` calls `_helper_B` which calls `_helper_C`, all three must be included in `func_A`'s example file.

Rules:
- **Prefer inlining over importing** — copy dependent functions verbatim into the file so it truly runs standalone
- Place dependencies above the target function in the file (definition order)
- If a dependency is a class method, include the minimal class skeleton needed
- Do NOT inline functions from external packages — use `import` for those
- Only fall back to `import` for truly complex cases (e.g., a dependency that itself pulls in 10+ other functions and external resources). Add a comment explaining why import was chosen over inline

### 3. Generate meaningful sample inputs

This is the most important step. The example data should help someone **immediately understand** what the function does and what kind of data it works with.

Guidelines:
- **Read the function body, docstring, and any schema/config files it references** to understand the domain
- Create realistic, domain-appropriate data (not `"test"` or `"foo"`)
- Add a `# --- Sample Input ---` comment block explaining what each variable represents
- For complex nested structures (dicts, JSON), use real-world-like field names and values from the project domain
- If the function reads files, create the sample data inline (as a string or tempfile) instead
- If the function needs an API client or network resource, create a **mock** or use the function's logic in a way that doesn't require the real resource
- For class methods, instantiate the class with realistic constructor arguments

Bad example input:
```python
data = {"a": 1, "b": 2}
result = my_func(data)
```

Good example input:
```python
# --- Sample Input ---
# A gene type definition from the extraction schema.
# "properties" maps field names to their schema (description, type, default).
gene_def = {
    "properties": {
        "Gene_Name": {
            "title": "Gene_Name",
            "description": "The name or symbol of the Core Gene, e.g., TaGS5, Pi2.",
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": "NA",
        },
        "Species": {
            "title": "Species",
            "description": "The main species studied (common name).",
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": "NA",
        },
    }
}

result = _schema_props_to_fc(gene_def)
```

### 4. Write the example file

Each `<func_name>.py` follows this template:

```python
"""
<func_name> — <one-line description of what the function does>

Source: <relative path to original file>:<line number>

Usage:
    python <func_name>.py
"""

# --- External Imports ---
import json  # (only what's actually needed)

# --- Inlined Dependencies ---
# (copied verbatim from source, with a comment noting origin)

def _helper_func(...):
    """(Inlined from source_file.py:35)"""
    ...

# --- Target Function ---

def target_func(...):
    """Original docstring..."""
    ...

# --- Sample Input ---
# Explanation of what this data represents and why it's structured this way.

sample_data = { ... }

# --- Run ---
if __name__ == "__main__":
    result = target_func(sample_data)
    print("=== Result ===")
    print(result)
    # For complex outputs, pretty-print:
    # print(json.dumps(result, indent=2, ensure_ascii=False))
```

### 5. Verify runnability

After generating all example files, run each one to confirm it executes without errors:

```bash
cd examples/extract/
python _schema_props_to_fc.py
python _build_extract_schema.py
# ... every file
```

If a file fails:
- Fix the issue (usually a missing import or dependency)
- Re-run to confirm
- Note: functions that inherently require external resources (API calls, database connections) should use mocks or stubs, and should still run without errors

### 6. Create an index

After all examples are generated, create `examples/README.md`:

```markdown
# Function Examples

Auto-generated standalone examples for every function.

## extract.py

| Function | Description | Run |
|----------|-------------|-----|
| `_schema_props_to_fc` | Convert gene type properties to FC format | `python extract/_schema_props_to_fc.py` |
| `_build_extract_schema` | Build OpenAI FC tool schema from a schema section | `python extract/_build_extract_schema.py` |
| ... | ... | ... |

## text_utils.py

| Function | Description | Run |
|----------|-------------|-----|
| `strip_images` | Remove markdown image tags | `python text_utils/strip_images.py` |
| ... | ... | ... |
```

## Edge Cases

### Functions that read from files
Create the file content as a string variable and use `io.StringIO` or `tempfile` to simulate file reading. Or if the function takes a file path, create a temp file in the example.

### Functions that call APIs
Replace the API client with a mock object that returns realistic sample data. Comment clearly that this is a mock.

### Functions with side effects (print, write files)
These are fine — the point is to see the function run. Just make sure file writes go to a temp directory or the example's own folder.

### Class methods
Include a minimal class definition with `__init__` and the target method. Instantiate with realistic data.

### Generators and async functions
Wrap generators in `list()` to show output. For async functions, use `asyncio.run()`.

## Quality Checklist

Before considering the task complete, verify:
- [ ] **Every** function has a corresponding `.py` file — strict 1:1, no skipping
- [ ] Files are at `examples/<source_name>/<func_name>.py`
- [ ] Each file runs successfully with `python <func_name>.py`
- [ ] Sample inputs are realistic and domain-appropriate (not placeholder junk)
- [ ] Internal dependencies are properly inlined (copied into the file)
- [ ] External imports are present
- [ ] Each file has a docstring explaining what the function does
- [ ] The README index is generated
