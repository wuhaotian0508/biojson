#!/bin/bash
# ═══════════════════════════════════════════════════════════
# NutriMaster Extractor Pipeline — Entry Script
# ═══════════════════════════════════════════════════════════
#
# Usage:
#   bash src/nutrimaster/extraction/run.sh                     # pipeline (default)
#   bash src/nutrimaster/extraction/run.sh pipeline            # full pipeline
#   bash src/nutrimaster/extraction/run.sh pipeline-test       # test: first file
#   bash src/nutrimaster/extraction/run.sh pipeline-test 3     # test: 3rd file
#   bash src/nutrimaster/extraction/run.sh pipeline-test name  # test: match filename
#   bash src/nutrimaster/extraction/run.sh rerun               # force re-run all
#   FORCE_RERUN=1 bash src/nutrimaster/extraction/run.sh       # force re-run
#
# ═══════════════════════════════════════════════════════════
#nohup bash src/nutrimaster/extraction/run.sh pipeline 2>&1 | tee src/nutrimaster/extraction/reports/pipeline_run_$(date +%Y%m%d_%H%M%S).md &


set -euo pipefail

# ─── Base paths ──────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_BASE_DIR="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
export BASE_DIR="${BASE_DIR:-${DEFAULT_BASE_DIR}}"
EXTRACTOR_DIR="${SCRIPT_DIR}"

# ─── Load .env ───────────────────────────────────────────
if [ -f "${BASE_DIR}/.env" ]; then
  set -a
  source "${BASE_DIR}/.env"
  set +a
fi

# ─── Directory config ────────────────────────────────────
export MD_DIR="${MD_DIR:-${EXTRACTOR_DIR}/input}"
export JSON_DIR="${JSON_DIR:-${BASE_DIR}/data/corpus}"
export REPORTS_DIR="${REPORTS_DIR:-${EXTRACTOR_DIR}/reports}"
export TOKEN_USAGE_DIR="${TOKEN_USAGE_DIR:-${EXTRACTOR_DIR}/reports/token-usage}"
export PROCESSED_DIR="${PROCESSED_DIR:-${MD_DIR}/processed}"

# ─── Prompt/Schema ───────────────────────────────────────
export PROMPT_PATH="${PROMPT_PATH:-${EXTRACTOR_DIR}/prompts/nutri_gene_prompt_v5.txt}"
export SCHEMA_PATH="${SCHEMA_PATH:-${EXTRACTOR_DIR}/prompts/nutri_gene_schema_v5.json}"

# ─── Model ───────────────────────────────────────────────
export EXTRACTOR_MODEL="${EXTRACTOR_MODEL:-gpt-5.5}"
export TEMPERATURE="${TEMPERATURE:-0.7}"

# ─── Concurrency ─────────────────────────────────────────
export MAX_WORKERS="${MAX_WORKERS:-20}"

# ─── Run mode ────────────────────────────────────────────
MODE="${1:-pipeline}"
TEST_INDEX="${2:-1}"

echo "═══════════════════════════════════════════════════════"
echo "🚀 NutriMaster Extractor Pipeline v4"
echo "   Mode:     ${MODE}"
echo "   Model:    ${EXTRACTOR_MODEL}"
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
    python -m nutrimaster.extraction.pipeline
    ;;
  pipeline-test)
    python -m nutrimaster.extraction.pipeline --test "${TEST_INDEX}"
    ;;
  rerun)
    export FORCE_RERUN=1
    python -m nutrimaster.extraction.pipeline
    ;;
  *)
    echo "❌ Unknown mode: ${MODE}"
    echo ""
    echo "Usage: bash src/nutrimaster/extraction/run.sh [mode] [test-index]"
    echo ""
    echo "  pipeline          Full pipeline (default)"
    echo "  pipeline-test     Test mode, process 1 file"
    echo "  pipeline-test 3   Test mode, 3rd file"
    echo "  rerun             Force re-run all files"
    exit 1
    ;;
esac
