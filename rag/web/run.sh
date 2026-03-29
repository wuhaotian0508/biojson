#!/bin/bash
# 开发模式启动脚本

echo "启动 RAG 基因问答系统 (开发模式)"
echo "========================================"

cd "$(dirname "$0")"
python app.py
