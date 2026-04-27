# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BioJSON is a scientific research pipeline for extracting structured gene information from plant nutrition metabolism literature. The system has two main components:

1. **Extractor Pipeline**: Converts scientific papers (Markdown) → structured JSON using LLM-based extraction and verification
2. **RAG System**: Provides question-answering capabilities over the extracted gene database using retrieval-augmented generation

**Core Goal**: Extract experimentally validated genes (enzymes, transporters, regulators) that control nutrient content in crops (vitamins, minerals, amino acids, carotenoids, etc.) from academic literature.

## Architecture

### Two-Stage Pipeline (Extractor)

```
Paper.md → Extract API → Raw JSON → Verify API (batched) → Validated JSON → rag/data/
```

- **Extract**: Single API call per paper extracts all genes + metadata (Title/Journal/DOI)
- **Verify**: Batched verification (10 genes per call) checks for hallucinations and corrects errors
- **Parallel Processing**: Papers processed concurrently using ThreadPoolExecutor (default: 20 workers)

### RAG Architecture

```
User Query → Agent (LLM) → Tool Selection → [RAG/PubMed/GeneDB/CRISPR/PersonalLib] → Response
```

- **Agent-based**: LLM-driven tool calling loop (not fixed pipeline)
- **Mode-aware**: Normal search vs. depth mode provide different tool sets
- **Skills System**: Pre-defined complex task workflows (SOP-like)
- **Personal Library**: User-uploaded PDF knowledge base with vector search

### Directory Structure

```
extractor/          # Paper → JSON extraction pipeline
├── pipeline.py     # Main orchestrator (parallel processing)
├── extract.py      # LLM extraction logic
├── verify.py       # Verification & correction logic
├── input/          # Input markdown files (MinerU-converted papers)
├── output/         # Generated JSON (deprecated, use rag/data/)
├── reports/        # Extraction/verification reports + token usage
├── prompts/        # Prompt templates & JSON schemas
└── run.sh          # Entry point script

rag/                # RAG question-answering system
├── core/           # Agent, LLM client, config
├── search/         # Retriever, reranker, query translation
├── tools/          # Tool implementations (PubMed, GeneDB, RAG, CRISPR, etc.)
├── skills/         # Skill definitions (complex workflows)
├── data/           # Gene JSON database (extractor output goes here)
├── index/          # Vector embeddings & BM25 index
├── web/            # FastAPI web UI (port 5000)
├── api/            # Lightweight API server (port 8000)
└── personal_lib/   # User-uploaded PDF library

admin/              # Admin panel (Flask blueprint)
data/               # Legacy data directory
docs/               # Documentation
scripts/            # Utility scripts
```

## Common Commands

### Extractor Pipeline

```bash
# Full pipeline (all papers in extractor/input/)
bash extractor/run.sh

# Test mode: process first file
bash extractor/run.sh pipeline-test

# Test mode: process 3rd file
bash extractor/run.sh pipeline-test 3

# Test mode: match filename (fuzzy)
bash extractor/run.sh pipeline-test Butelli

# Force re-run all files (ignore existing outputs)
bash extractor/run.sh rerun
# or
FORCE_RERUN=1 bash extractor/run.sh

# Custom parallelism
MAX_WORKERS=5 bash extractor/run.sh
```

**Output**: JSON files written to `rag/data/` (not `extractor/output/`)

### RAG System

```bash
# Web UI (development mode with auto-reload)
cd rag/web
bash run.sh
# Access at http://localhost:5000

# Web UI (production mode with gunicorn)
cd rag/web
bash run_prod.sh

# Lightweight API server (for testing/integration)
cd rag
bash api/start.sh
# Access at http://localhost:8000
# Endpoints: POST /api/query, POST /api/query/stream, GET /api/health
```

### Testing

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest extractor/tests/test_pipeline_runtime.py
python -m pytest rag/tests/test_experiment_pipeline.py

# Run with verbose output
python -m pytest -v

# Run tests in specific directory
python -m pytest extractor/tests/
python -m pytest rag/tests/
```

### Development

```bash
# Install dependencies (using uv)
uv sync

# Or using pip
pip install -e .

# Install with optional dependencies
pip install -e ".[dev]"      # Full dev environment
pip install -e ".[pdf]"       # PDF parsing for personal library
pip install -e ".[index]"     # TF-IDF indexing
```

## Configuration

### Environment Variables

Required variables in `.env` (see `.env.example`):

```bash
# LLM API (primary)
API_KEY=your-api-key
BASE_URL=https://api.example.com/v1
MODEL=Vendor2/Claude-4.6-opus

# LLM API (fallback, optional)
FALLBACK_API_KEY=
FALLBACK_BASE_URL=
FALLBACK_MODEL=

# Retrieval & Embeddings
JINA_API_KEY=your-jina-key

# Supabase (for web auth)
SUPABASE_URL=
SUPABASE_KEY=

# Email (for verification codes)
SMTP_SERVER=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=
```

### Extractor Configuration

Environment variables (can be set in `.env` or passed to `run.sh`):

```bash
MD_DIR=extractor/input              # Input markdown directory
JSON_DIR=rag/data                   # Output JSON directory (NOT extractor/output!)
REPORTS_DIR=extractor/reports       # Reports directory
PROMPT_PATH=extractor/prompts/nutri_gene_prompt_v5.txt
SCHEMA_PATH=extractor/prompts/nutri_gene_schema_v5.json
MODEL=Vendor2/Claude-4.6-opus
TEMPERATURE=0.7
MAX_WORKERS=20                      # Parallel processing workers
```

### RAG Configuration

See `rag/core/config.py` for defaults. Key settings:

- **Retrieval**: Top-k results, reranking, BM25 + vector hybrid search
- **Agent**: Max iterations, tool timeout, depth mode settings
- **Skills**: System skills directory, user skills directory

## Key Concepts

### Gene Extraction Schema

Each paper produces a JSON with:
- **Metadata**: Title, Journal, DOI, Year, Authors
- **Genes**: Array of gene objects (37+ fields each)
  - Gene identity: Name, Aliases, Species, Accession
  - Pathway info: Metabolic pathway, enzyme class, substrates/products
  - Phenotype: Nutrient affected, direction (increase/decrease), magnitude
  - Validation: Methods used, genetic perturbation type
  - Variants: Natural/engineered variants, breeding value

### Gene Categories

The schema supports three gene function categories (auto-selected during extraction):
- **Pathway**: Metabolic enzymes directly synthesizing nutrients
- **Regulation**: Transcription factors, signaling proteins
- **Common**: Fields shared by both categories

### Verification Strategy

Two-stage verification to reduce LLM hallucinations:
1. **Field-level verification**: Check each field against source text
2. **Correction**: If hallucination detected, re-extract with focused prompt
3. **Batching**: Process 10 genes per API call for efficiency

### RAG Agent Architecture

- **Agent Loop**: LLM decides which tools to call based on query
- **Tool Registry**: Dynamically filtered by mode (normal vs. depth)
- **Skills**: Pre-defined workflows for complex tasks (e.g., "literature review SOP")
- **Context Management**: Conversation history + tool results fed back to LLM

### Personal Library

Users can upload PDFs to build a personal knowledge base:
- PDFs parsed with PyMuPDF
- Chunked and embedded with Jina
- Searchable via `PersonalLibSearchTool`
- Isolated per user (requires authentication)

## Important Notes

- **Output Location**: Extractor writes to `rag/data/`, NOT `extractor/output/` (legacy)
- **Schema Versions**: Current version is v5 (`nutri_gene_schema_v5.json`)
- **Parallel Safety**: Pipeline uses file locks to prevent concurrent writes to same file
- **Token Tracking**: All API calls logged to `extractor/reports/token-usage/`
- **RAG Data Source**: RAG system reads from `rag/data/*.json` (extractor output)
- **Schema Mismatch**: RAG and extractor schemas are currently aligned (both use v5)
- **Test Mode**: Always test with `pipeline-test` before running full pipeline on new prompts/schemas
- **Model Fallback**: If primary model fails, system automatically tries fallback model (if configured)

## Troubleshooting

### Extractor Issues

- **"File already processed"**: Use `FORCE_RERUN=1` or `bash extractor/run.sh rerun`
- **API timeout**: Reduce `MAX_WORKERS` or check network/API status
- **Schema validation errors**: Check `extractor/reports/` for detailed error messages
- **Empty gene arrays**: Check if paper actually contains relevant genes (not all papers do)

### RAG Issues

- **"JINA_API_KEY not found"**: Set in `.env`, no default fallback
- **Retrieval returns no results**: Check if `rag/data/` contains JSON files and `rag/index/` has embeddings
- **Agent loops infinitely**: Check `max_iterations` in config, review tool outputs for errors
- **Personal library not working**: Ensure PyMuPDF installed (`pip install -e ".[pdf]"`)

### Web UI Issues

- **Port already in use**: Kill existing process (`lsof -t -i:5000 | xargs kill -9`)
- **Authentication fails**: Check Supabase credentials in `.env`
- **Static files not loading**: Ensure `rag/web/static/` exists and is readable

## Development Workflow

1. **Add new papers**: Place markdown files in `extractor/input/processed/`
2. **Test extraction**: `bash extractor/run.sh pipeline-test <filename>`
3. **Review reports**: Check `extractor/reports/` for extraction quality
4. **Run full pipeline**: `bash extractor/run.sh` (outputs to `rag/data/`)
5. **Rebuild RAG index**: Index automatically rebuilds on startup or use rebuild daemon
6. **Test RAG**: Start web UI and query the new data

## Performance

- **Extraction**: ~2-5 minutes per paper (depends on paper length and gene count)
- **Verification**: ~30 seconds per 10 genes
- **Parallel Processing**: 20 workers can process ~100 papers in 30-60 minutes
- **RAG Query**: ~2-5 seconds for normal mode, ~10-30 seconds for depth mode
- **Index Building**: ~1-2 minutes for 1000 genes (BM25 + vector embeddings)
