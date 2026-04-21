#!/bin/bash
# RAG API 快速启动脚本

set -e

cd "$(dirname "$0")/.."

echo "=========================================="
echo "RAG API Server"
echo "=========================================="
echo ""

# 检查 .env 文件
if [ ! -f "../.env" ]; then
    echo "❌ 错误: 未找到 .env 文件"
    echo "请先配置 .env 文件（参考 .env.example）"
    exit 1
fi

# 默认参数
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

echo "启动配置:"
echo "  - 监听地址: $HOST:$PORT"
echo "  - 工作目录: $(pwd)"
echo ""

# 启动服务
python -m api.server --host "$HOST" --port "$PORT" "$@"
