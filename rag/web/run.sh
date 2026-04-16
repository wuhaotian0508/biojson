#!/bin/bash
# 开发模式启动脚本 (uv + uvicorn)
# 优雅清理旧进程
OLD_PIDS=$(lsof -t -i:5000 2>/dev/null || true)
if [ -n "$OLD_PIDS" ]; then
  kill -9 $OLD_PIDS
fi

echo "启动 RAG 基因问答系统 (开发模式 - uvicorn)"
echo "========================================"

cd "$(dirname "$0")"
export PYTHONUNBUFFERED=1
exec uv run uvicorn app:app --host 0.0.0.0 --port 5000 --reload
