#!/bin/bash
# ═══════════════════════════════════════════════════════════
# BioJSON Pipeline - 统一配置与运行脚本
# ═══════════════════════════════════════════════════════════
#
# 用法:
#   bash scripts/run.sh              # 默认: 提取 + 验证（全量）
#   bash scripts/run.sh extract      # 仅提取 MD → JSON
#   bash scripts/run.sh verify       # 仅验证 JSON
#   bash scripts/run.sh all          # 提取 + 验证（全量）
#   bash scripts/run.sh test         # 测试模式: 仅处理第 1 个文件
#   bash scripts/run.sh test 3       # 测试模式: 仅处理第 3 个文件
#   bash scripts/run.sh rerun        # 强制全部重跑（忽略已有结果）
#   FORCE_RERUN=1 bash scripts/run.sh extract  # 强制重跑提取
#
# ═══════════════════════════════════════════════════════════

# ─── 基础路径 ─────────────────────────────────────────────
export BASE_DIR="/data/haotianwu/biojson"
export MD_DIR="${BASE_DIR}/md"
export JSON_DIR="${BASE_DIR}/json"
export RAW_EXTRACTIONS_DIR="${BASE_DIR}/reports/raw_extractions"
export VERIFICATIONS_DIR="${BASE_DIR}/reports/verifications"
export EXTRACT_TOKENS_DIR="${BASE_DIR}/reports/extract_tokens"
export VERIFY_TOKENS_DIR="${BASE_DIR}/reports/verify_tokens"
export PROCESSED_DIR="${MD_DIR}/processed"

# ─── 配置文件 ─────────────────────────────────────────────
export PROMPT_PATH="${BASE_DIR}/configs/nutri_plant.txt"
export SCHEMA_PATH="${BASE_DIR}/configs/nutri_plant.json"

# ─── 模型参数 ─────────────────────────────────────────────
export MODEL="${MODEL:-Vendor2/Claude-4.6-opus}"
export TEMPERATURE="${TEMPERATURE:-0.7}"

# ─── 运行模式 ─────────────────────────────────────────────
MODE="${1:-all}"
TEST_INDEX="${2:-1}"

echo "═══════════════════════════════════════════════════════"
echo "🚀 BioJSON Pipeline"
echo "   模式:     ${MODE}"
echo "   模型:     ${MODEL}"
echo "   输入目录: ${MD_DIR}"
echo "   输出目录: ${JSON_DIR}"
if [ "$MODE" = "test" ]; then
echo "   测试文件: 第 ${TEST_INDEX} 个"
fi
if [ "${FORCE_RERUN}" = "1" ]; then
echo "   ⚡ 强制重跑: 忽略已有结果"
else
echo "   📋 增量模式: 跳过已处理的文件"
fi
echo "═══════════════════════════════════════════════════════"
echo ""

case $MODE in
  extract)
    python scripts/md_to_json.py
    ;;
  verify)
    python scripts/verify_response.py
    ;;
  all)
    python scripts/md_to_json.py && python scripts/verify_response.py
    ;;
  test)
    export TEST_MODE=1
    export TEST_INDEX="${TEST_INDEX}"
    python scripts/md_to_json.py && python scripts/verify_response.py
    ;;
  rerun)
    export FORCE_RERUN=1
    python scripts/md_to_json.py && python scripts/verify_response.py
    ;;
  *)
    echo "❌ 未知模式: ${MODE}"
    echo ""
    echo "用法: bash scripts/run.sh [extract|verify|all|test] [文件编号]"
    echo ""
    echo "  extract      仅提取 MD → JSON"
    echo "  verify       仅验证 JSON"
    echo "  all          提取 + 验证（默认）"
    echo "  test         测试模式，仅处理 1 个文件"
    echo "  test 3       测试模式，处理第 3 个文件"
    echo "  rerun        强制全部重跑（忽略已有结果）"
    exit 1
    ;;
esac
