#!/bin/bash
# ═══════════════════════════════════════════════════════════
# BioJSON Extractor Pipeline — Entry Script
# ═══════════════════════════════════════════════════════════
#
# Usage:
#   bash extractor/run.sh                     # pipeline (default)
#   bash extractor/run.sh pipeline            # full pipeline
#   bash extractor/run.sh pipeline-test       # test: first file
#   bash extractor/run.sh pipeline-test 3     # test: 3rd file
#   bash extractor/run.sh pipeline-test name  # test: match filename
#   bash extractor/run.sh rerun               # force re-run all
#   FORCE_RERUN=1 bash extractor/run.sh       # force re-run
#
# ═══════════════════════════════════════════════════════════

set -euo pipefail

# ─── Base paths ──────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
export BASE_DIR="${BASE_DIR:-${DEFAULT_BASE_DIR}}"
EXTRACTOR_DIR="${BASE_DIR}/extractor"

# ─── Load .env ───────────────────────────────────────────
if [ -f "${BASE_DIR}/.env" ]; then
  set -a
  source "${BASE_DIR}/.env"
  set +a
fi

# ─── Directory config ────────────────────────────────────
export MD_DIR="${MD_DIR:-${EXTRACTOR_DIR}/input}"
export JSON_DIR="${JSON_DIR:-${EXTRACTOR_DIR}/output}"
export REPORTS_DIR="${REPORTS_DIR:-${EXTRACTOR_DIR}/reports}"
export TOKEN_USAGE_DIR="${TOKEN_USAGE_DIR:-${EXTRACTOR_DIR}/reports/token-usage}"
export PROCESSED_DIR="${PROCESSED_DIR:-${MD_DIR}/processed}"

# ─── Prompt/Schema ───────────────────────────────────────
export PROMPT_PATH="${PROMPT_PATH:-${EXTRACTOR_DIR}/prompts/nutri_gene_prompt_v4.txt}"
export SCHEMA_PATH="${SCHEMA_PATH:-${EXTRACTOR_DIR}/prompts/nutri_gene_schema_v4.json}"

# ─── Model ───────────────────────────────────────────────
export MODEL="${MODEL:-Vendor2/Claude-4.6-opus}"
export TEMPERATURE="${TEMPERATURE:-0.7}"

# ─── Fallback ────────────────────────────────────────────
export FALLBACK_API_KEY="${FALLBACK_API_KEY:-}"
export FALLBACK_BASE_URL="${FALLBACK_BASE_URL:-}"
export FALLBACK_MODEL="${FALLBACK_MODEL:-}"

# ─── Concurrency ─────────────────────────────────────────
export MAX_WORKERS="${MAX_WORKERS:-3}"

# ─── Run mode ────────────────────────────────────────────
MODE="${1:-pipeline}"
TEST_INDEX="${2:-1}"

echo "═══════════════════════════════════════════════════════"
echo "🚀 BioJSON Extractor Pipeline v4"
echo "   Mode:     ${MODE}"
echo "   Model:    ${MODEL}"
echo "   Input:    ${MD_DIR}"
echo "   Output:   ${JSON_DIR}"
echo "   Workers:  ${MAX_WORKERS}"
if [ "$MODE" = "pipeline-test" ]; then
  echo "   Test:     ${TEST_INDEX}"
fi
echo "═══════════════════════════════════════════════════════"
echo ""

cd "${BASE_DIR}"

case $MODE in
  pipeline)
    python -m extractor.pipeline
    ;;
  pipeline-test)
    python -m extractor.pipeline --test "${TEST_INDEX}"
    ;;
  rerun)
    export FORCE_RERUN=1
    python -m extractor.pipeline
    ;;
  *)
    echo "❌ Unknown mode: ${MODE}"
    echo ""
    echo "Usage: bash extractor/run.sh [mode] [test-index]"
    echo ""
    echo "  pipeline          Full pipeline (default)"
    echo "  pipeline-test     Test mode, process 1 file"
    echo "  pipeline-test 3   Test mode, 3rd file"
    echo "  rerun             Force re-run all files"
    exit 1
    ;;
esac
