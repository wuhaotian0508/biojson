#!/bin/bash
# 生产模式启动脚本 (uv + uvicorn multi-worker)
OLD_PIDS=$(lsof -t -i:5000 2>/dev/null || true)
if [ -n "$OLD_PIDS" ]; then
  kill -9 $OLD_PIDS
fi

echo "启动 RAG 基因问答系统 (生产模式 - uvicorn)"
echo "========================================"

cd "$(dirname "$0")"
export PYTHONUNBUFFERED=1
# 部分 HTTPS 站点走 clash 会 TLS 超时，直连反而正常，加入 no_proxy
export no_proxy="${no_proxy:+$no_proxy,}supabase.co,ncbi.nlm.nih.gov"
export NO_PROXY="$no_proxy"
exec uv run uvicorn app:app --host 0.0.0.0 --port 5000 --workers 4 --timeout-keep-alive 300
