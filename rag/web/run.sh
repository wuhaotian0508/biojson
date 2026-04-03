#!/bin/bash
# 开发模式启动脚本
# 优雅清理旧进程
kill -9 $(lsof -t -i:5000)
OLD_PID=$(lsof -t -i:5000 2>/dev/null)
if [ -n "$OLD_PID" ]; then
  kill -9 "$OLD_PID"
fi

echo "启动 RAG 基因问答系统 (开发模式)"
echo "========================================"

cd "$(dirname "$0")"
python app.py
