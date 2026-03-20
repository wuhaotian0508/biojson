#!/bin/bash
# ═══════════════════════════════════════════════════════════
# BioJSON Pipeline - 统一配置与运行脚本
# ═══════════════════════════════════════════════════════════
#
# 用法:
#   bash scripts/run.sh              # 默认: pipeline（提取+验证，2次API/篇）
#   bash scripts/run.sh pipeline     # 新流水线（推荐，2次API/篇）
#   bash scripts/run.sh pipeline-test    # pipeline 测试模式（第1个文件）
#   bash scripts/run.sh pipeline-test 3  # pipeline 测试模式（第3个文件）
#   bash scripts/run.sh pipeline-test new # pipeline 测试模式（按名匹配）
#   bash scripts/run.sh extract      # 仅提取 MD → JSON（旧模式）
#   bash scripts/run.sh verify       # 仅验证 JSON（旧模式）
#   bash scripts/run.sh all          # 提取 + 验证（旧模式）
#   bash scripts/run.sh test         # 测试模式: 仅处理第 1 个文件（旧模式）
#   bash scripts/run.sh test 3       # 测试模式: 仅处理第 3 个文件
#   bash scripts/run.sh test new     # 测试模式: 按文件名匹配（可省略 .md）
#   bash scripts/run.sh rerun        # 强制全部重跑（忽略已有结果）
#   bash scripts/run.sh rollback plcell  # 回退指定文件（删除 JSON，移回 MD）
#   FORCE_RERUN=1 bash scripts/run.sh pipeline  # 强制重跑
#
# ═══════════════════════════════════════════════════════════

# ─── 基础路径 ─────────────────────────────────────────────
export BASE_DIR="/data/haotianwu/biojson"

# ─── 加载 .env 敏感配置（API Key 等，不上传 GitHub）──────
if [ -f "${BASE_DIR}/.env" ]; then
  set -a
  source "${BASE_DIR}/.env"
  set +a
fi
export MD_DIR="${BASE_DIR}/md"
export JSON_DIR="${BASE_DIR}/json"
export REPORTS_DIR="${BASE_DIR}/reports"
export TOKEN_USAGE_DIR="${BASE_DIR}/token-usage"
export PROCESSED_DIR="${MD_DIR}/processed"

# ─── 配置文件 ─────────────────────────────────────────────
export PROMPT_PATH="${BASE_DIR}/configs/nutri_gene_prompt_v2.txt"
export SCHEMA_PATH="${BASE_DIR}/configs/nutri_gene_schema_v2.json"

# ─── 模型参数 ─────────────────────────────────────────────
export MODEL="${MODEL:-Vendor2/Claude-4.6-opus}"
export TEMPERATURE="${TEMPERATURE:-0.7}"

# ─── Fallback 模型（当主 API 因危险词被拦截时自动切换）────
# 密钥从 .env 读取，不硬编码（防止泄露到 GitHub）
export FALLBACK_API_KEY="${FALLBACK_API_KEY:-}"
export FALLBACK_BASE_URL="${FALLBACK_BASE_URL:-}"
export FALLBACK_MODEL="${FALLBACK_MODEL:-}"

# ─── 运行模式 ─────────────────────────────────────────────
MODE="${1:-pipeline}"
TEST_INDEX="${2:-1}"

echo "═══════════════════════════════════════════════════════"
echo "🚀 BioJSON Pipeline"
echo "   模式:     ${MODE}"
echo "   模型:     ${MODEL}"
echo "   输入目录: ${MD_DIR}"
echo "   输出目录: ${JSON_DIR}"
if [ "$MODE" = "test" ] || [ "$MODE" = "pipeline-test" ]; then
  if [[ "${TEST_INDEX}" =~ ^[0-9]+$ ]]; then
    echo "   测试文件: 第 ${TEST_INDEX} 个"
  else
    echo "   测试文件: ${TEST_INDEX}"
  fi
fi
if [ "$MODE" = "rollback" ]; then
  echo "   回退目标: ${TEST_INDEX}"
fi
if [ "${FORCE_RERUN}" = "1" ]; then
echo "   ⚡ 强制重跑: 忽略已有结果"
else
echo "   📋 增量模式: 跳过已处理的文件"
fi
echo "═══════════════════════════════════════════════════════"
echo ""

case $MODE in
  pipeline)
    python scripts/pipeline.py
    ;;
  pipeline-test)
    export TEST_MODE=1
    export TEST_INDEX="${TEST_INDEX}"
    python scripts/pipeline.py
    ;;
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
    python scripts/pipeline.py
    ;;
  rollback)
    export ROLLBACK_TARGET="${TEST_INDEX}"
    python scripts/rollback.py
    ;;
  *)
    echo "❌ 未知模式: ${MODE}"
    echo ""
    echo "用法: bash scripts/run.sh [模式] [编号或文件名]"
    echo ""
    echo "  ★ 推荐（新流水线，2次API/篇）:"
    echo "  pipeline         提取 + 验证（默认）"
    echo "  pipeline-test    测试模式，仅处理 1 个文件"
    echo "  pipeline-test 3  测试模式，处理第 3 个文件"
    echo "  pipeline-test new 测试模式，按文件名匹配"
    echo ""
    echo "  旧模式（兼容）:"
    echo "  extract      仅提取 MD → JSON"
    echo "  verify       仅验证 JSON"
    echo "  all          提取 + 验证"
    echo "  test         测试模式（旧流程）"
    echo "  rerun        强制全部重跑"
    echo "  rollback X   回退指定文件"
    exit 1
    ;;
esac
