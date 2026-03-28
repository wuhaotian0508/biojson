# Function Examples

Auto-generated standalone examples for every function in `extractor/text_utils.py`.

## text_utils.py

| Function | Description | Run |
|----------|-------------|-----|
| `strip_images` | Remove markdown image tags (CDN and local paths) | `python text_utils/strip_images.py` |
| `strip_urls` | Remove parenthesized HTTP/HTTPS URLs | `python text_utils/strip_urls.py` |
| `strip_references` | Remove References / Literature Cited section | `python text_utils/strip_references.py` |
| `strip_acknowledgments` | Remove Acknowledgments section | `python text_utils/strip_acknowledgments.py` |
| `strip_extra_blanks` | Collapse 3+ consecutive blank lines to 2 | `python text_utils/strip_extra_blanks.py` |
| `_split_sections` | Split markdown by top-level `# ` headings into (heading, body) tuples | `python text_utils/_split_sections.py` |
| `_classify_headings_with_llm` | Call LLM API to classify which headings to remove (uses mock) | `python text_utils/_classify_headings_with_llm.py` |
| `extract_relevant_sections` | Filter out irrelevant sections using LLM classification (uses mock) | `python text_utils/extract_relevant_sections.py` |
| `preprocess_md` | One-stop preprocessing entry point: strip images, URLs, blanks, and irrelevant sections (uses mock) | `python text_utils/preprocess_md.py` |
