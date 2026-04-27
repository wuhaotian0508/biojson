#!/usr/bin/env bash
# 后台启动 RAG 全量重建，脱离终端运行（nohup + setsid），
# SSH 断开不会终止进程。
#
# 日志：/data/haotianwu/biojson/rag/logs/rebuild.log
# PID ：/data/haotianwu/biojson/rag/logs/rebuild.pid
#
# 用法：
#   bash rag/scripts/run_rebuild_daemon.sh            # 增量（默认）
#   bash rag/scripts/run_rebuild_daemon.sh --force    # 丢弃旧索引全量重建
#
# 监控：
#   tail -f rag/logs/rebuild.log
#
# 停止：
#   kill $(cat rag/logs/rebuild.pid)
#   （再次运行本脚本会自动从 checkpoint 续传）

set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$HERE/logs"
mkdir -p "$LOG_DIR"

LOG="$LOG_DIR/rebuild.log"
PIDFILE="$LOG_DIR/rebuild.pid"

# 检查是否已经在跑
if [[ -f "$PIDFILE" ]]; then
    old_pid="$(cat "$PIDFILE" || true)"
    if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
        echo "[run_rebuild_daemon] 发现运行中进程 PID=$old_pid，不再启动新进程。"
        echo "  查看日志: tail -f $LOG"
        echo "  停止它  : kill $old_pid"
        exit 0
    fi
    rm -f "$PIDFILE"
fi

ARGS="$*"

echo "[run_rebuild_daemon] 启动重建守护进程..."
echo "  工作目录: $HERE"
echo "  参数    : $ARGS"
echo "  日志    : $LOG"
echo "  PID 文件: $PIDFILE"

cd "$HERE"

# setsid + nohup 双保险：脱离终端会话 → SSH 断开也不会收到 SIGHUP
setsid nohup python -u -m scripts.rebuild_index $ARGS \
    >> "$LOG" 2>&1 < /dev/null &

NEW_PID=$!
echo "$NEW_PID" > "$PIDFILE"

# 等几秒看有没有立即挂掉
sleep 2
if kill -0 "$NEW_PID" 2>/dev/null; then
    echo "[run_rebuild_daemon] 已启动 PID=$NEW_PID"
    echo ""
    echo "实时查看日志："
    echo "  tail -f $LOG"
    echo ""
    echo "停止进程："
    echo "  kill $NEW_PID   # 或 kill \$(cat $PIDFILE)"
    echo ""
    echo "恢复进程（会自动从 checkpoint 续传）："
    echo "  bash $0"
else
    echo "[run_rebuild_daemon] 启动后立即退出，检查日志: $LOG"
    tail -20 "$LOG" || true
    rm -f "$PIDFILE"
    exit 1
fi
