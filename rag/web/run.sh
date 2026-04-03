#!/bin/bash
# 开发模式启动脚本
# 优雅清理旧进程
lsof -ti:5000 | xargs kill -9
OLD_PIDS=$(lsof -t -i:5000 2>/dev/null || true)
if [ -n "$OLD_PIDS" ]; then
  kill -9 $OLD_PIDS
fi

echo "启动 RAG 基因问答系统 (开发模式)"
echo "========================================"

cd "$(dirname "$0")"
export PYTHONUNBUFFERED=1
exec python -u app.py
