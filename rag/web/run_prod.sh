#!/bin/bash
# 生产模式启动脚本

echo "启动 RAG 基因问答系统 (生产模式)"
echo "========================================"

cd "$(dirname "$0")"

# 使用 gunicorn 启动
gunicorn -w 4 -b 0.0.0.0:5000 \
    --timeout 300 \
    --access-logfile - \
    --error-logfile - \
    app:app
