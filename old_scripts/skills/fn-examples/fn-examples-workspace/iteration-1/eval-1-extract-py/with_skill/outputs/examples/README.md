# Function Examples

Auto-generated standalone examples for every function in `extractor/extract.py`.

Each `.py` file is independently runnable with `python <name>.py` — no project imports or external API keys required. API calls are mocked, file reads use temp files.

## extract.py

| Function | Description | Run |
|----------|-------------|-----|
| `_load_prompt` | Load the extraction prompt text from a file | `python extract/_load_prompt.py` |
| `_schema_props_to_fc` | Convert gene type properties to FC-compatible format | `python extract/_schema_props_to_fc.py` |
| `_build_extract_schema` | Build an OpenAI FC tool schema from a schema section | `python extract/_build_extract_schema.py` |
| `_build_classify_schema` | Build the classify_genes FC schema (inline) | `python extract/_build_classify_schema.py` |
| `_load_extract_schemas` | Load all extraction tool schemas from schema JSON file | `python extract/_load_extract_schemas.py` |
| `_build_extract_all_schema` | Build the extract_all_genes FC schema from MultipleGeneExtraction | `python extract/_build_extract_all_schema.py` |
| `_load_extract_all_schema` | Load the single extract_all_genes schema from file | `python extract/_load_extract_all_schema.py` |
| `_handle_extract_all` | Process extract_all_genes result into extraction dict + gene dict | `python extract/_handle_extract_all.py` |
| `_handle_classify` | Process classify_genes result with category normalization | `python extract/_handle_classify.py` |
| `_handle_extract` | Process extract_*_genes result into a gene array | `python extract/_handle_extract.py` |
| `_safe_parse_json` | Parse JSON with automatic truncation repair | `python extract/_safe_parse_json.py` |
| `_message_to_dict` | Convert OpenAI message object to serializable dict | `python extract/_message_to_dict.py` |
| `stem_to_dirname` | Convert markdown file stem to report directory name | `python extract/stem_to_dirname.py` |
| `_call_extract_api` | Single-step API extraction using extract_all_genes (mocked) | `python extract/_call_extract_api.py` |
| `extract_paper` | Full paper extraction pipeline entry point (mocked) | `python extract/extract_paper.py` |
