#!/bin/bash
# ============================================================
# dev.sh — BioJSON 本地开发一键启动脚本
# ============================================================
#
# 功能：
#   1. 自动检测端口占用并处理冲突（kill 占用进程或切换端口）
#   2. 同时启动 Web 前端（Next.js dev server）
#   3. 所有服务启动就绪后，自动打开浏览器
#   4. 脚本自行 cd 到目标目录，无需手动切换
#   5. Ctrl+C 一键停止所有服务
#
# 使用方法：
#   bash scripts/dev.sh              # 默认端口 3000
#   bash scripts/dev.sh --port 3001  # 指定端口
#   bash scripts/dev.sh --kill       # 强制 kill 占用端口的进程后启动
#
# 环境要求：
#   - Node.js 18+
#   - npm 依赖已安装（cd web && npm install）
#   - web/.env.local 已配置 Supabase 凭据
#
# ============================================================

set -e

# ── 颜色定义 ────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ── 自动定位项目根目录 ──────────────────────────────────────
# 无论从哪里调用，都能正确 cd 到项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WEB_DIR="$PROJECT_ROOT/web"

cd "$PROJECT_ROOT"
echo -e "${BLUE}📂 项目根目录: ${PROJECT_ROOT}${NC}"

# ── 默认配置 ────────────────────────────────────────────────
WEB_PORT=3000
FORCE_KILL=false

# ── 解析命令行参数 ──────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            WEB_PORT="$2"
            shift 2
            ;;
        --kill)
            FORCE_KILL=true
            shift
            ;;
        --help|-h)
            echo "用法: bash scripts/dev.sh [选项]"
            echo ""
            echo "选项:"
            echo "  --port <端口>   指定 Web 前端端口（默认: 3000）"
            echo "  --kill          强制 kill 占用端口的进程"
            echo "  --help, -h      显示帮助信息"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ 未知参数: $1${NC}"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# ── 子进程 PID 追踪（用于 Ctrl+C 清理）─────────────────────
PIDS=()

cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 正在停止所有服务...${NC}"
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
            wait "$pid" 2>/dev/null
        fi
    done
    echo -e "${GREEN}✅ 所有服务已停止${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# ── 端口检测与处理 ──────────────────────────────────────────
check_and_free_port() {
    local port=$1
    local service_name=$2

    # 检测端口是否被占用
    local pid=$(lsof -ti :$port 2>/dev/null || true)

    if [ -n "$pid" ]; then
        local process_info=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
        echo -e "${YELLOW}⚠️  端口 ${port} 已被占用（PID: ${pid}, 进程: ${process_info}）${NC}"

        if [ "$FORCE_KILL" = true ]; then
            echo -e "${YELLOW}🔪 强制终止占用进程 (--kill 模式)...${NC}"
            kill -9 $pid 2>/dev/null || true
            sleep 1
            echo -e "${GREEN}✅ 端口 ${port} 已释放${NC}"
        else
            # 尝试找一个空闲端口
            local new_port=$port
            while [ -n "$(lsof -ti :$new_port 2>/dev/null || true)" ]; do
                new_port=$((new_port + 1))
                if [ $new_port -gt $((port + 10)) ]; then
                    echo -e "${RED}❌ 端口 ${port}-${new_port} 全部被占用，请使用 --kill 参数或手动释放端口${NC}"
                    exit 1
                fi
            done

            if [ $new_port -ne $port ]; then
                echo -e "${CYAN}🔄 自动切换到空闲端口: ${new_port}${NC}"
            fi

            # 返回可用端口
            eval "${service_name}_PORT=${new_port}"
            return
        fi
    fi

    eval "${service_name}_PORT=${port}"
}

# ── 检查依赖 ────────────────────────────────────────────────
echo -e "\n${BLUE}🔍 检查环境...${NC}"

# 检查 Node.js
if ! command -v node &>/dev/null; then
    echo -e "${RED}❌ 未找到 Node.js，请先安装 Node.js 18+${NC}"
    exit 1
fi
echo -e "  Node.js: $(node --version)"

# 检查 npm
if ! command -v npm &>/dev/null; then
    echo -e "${RED}❌ 未找到 npm${NC}"
    exit 1
fi
echo -e "  npm: $(npm --version)"

# 检查 web 目录
if [ ! -d "$WEB_DIR" ]; then
    echo -e "${RED}❌ 找不到 web/ 目录: ${WEB_DIR}${NC}"
    exit 1
fi

# 检查 node_modules
if [ ! -d "$WEB_DIR/node_modules" ]; then
    echo -e "${YELLOW}📦 首次运行，安装 npm 依赖...${NC}"
    cd "$WEB_DIR" && npm install
    cd "$PROJECT_ROOT"
fi

# 检查 .env.local
if [ ! -f "$WEB_DIR/.env.local" ]; then
    echo -e "${RED}❌ 缺少 web/.env.local 配置文件${NC}"
    echo -e "   请复制模板并填入 Supabase 凭据:"
    echo -e "   cp web/.env.local.example web/.env.local"
    exit 1
fi

# ── 端口检测 ────────────────────────────────────────────────
echo -e "\n${BLUE}🔌 检测端口...${NC}"
check_and_free_port $WEB_PORT "WEB"
FINAL_WEB_PORT=$WEB_PORT

echo -e "  Web 前端: http://localhost:${FINAL_WEB_PORT}"

# ── 启动 Web 前端 (Next.js) ─────────────────────────────────
echo -e "\n${BLUE}🚀 启动 Web 前端 (Next.js dev server)...${NC}"
cd "$WEB_DIR"
PORT=$FINAL_WEB_PORT npm run dev &
WEB_PID=$!
PIDS+=($WEB_PID)
cd "$PROJECT_ROOT"

# ── 等待服务就绪 ────────────────────────────────────────────
echo -e "\n${YELLOW}⏳ 等待服务启动...${NC}"

wait_for_port() {
    local port=$1
    local name=$2
    local max_wait=30
    local waited=0

    while ! curl -s "http://localhost:${port}" >/dev/null 2>&1; do
        sleep 1
        waited=$((waited + 1))
        if [ $waited -ge $max_wait ]; then
            echo -e "${RED}❌ ${name} 启动超时（${max_wait}秒）${NC}"
            cleanup
            exit 1
        fi
        # 检查进程是否还在运行
        if ! kill -0 $WEB_PID 2>/dev/null; then
            echo -e "${RED}❌ ${name} 进程意外退出${NC}"
            cleanup
            exit 1
        fi
        printf "."
    done
    echo ""
    echo -e "  ${GREEN}✅ ${name} 就绪 (${waited}s)${NC}"
}

wait_for_port $FINAL_WEB_PORT "Web 前端"

# ── 自动打开浏览器 ──────────────────────────────────────────
URL="http://localhost:${FINAL_WEB_PORT}"
echo -e "\n${GREEN}============================================================${NC}"
echo -e "${GREEN}🎉 所有服务启动成功！${NC}"
echo -e "${GREEN}============================================================${NC}"
echo -e ""
echo -e "  🌐 Web 前端:  ${CYAN}${URL}${NC}"
echo -e ""
echo -e "  按 ${YELLOW}Ctrl+C${NC} 停止所有服务"
echo -e "${GREEN}============================================================${NC}"

# 尝试打开浏览器（兼容 Linux / macOS）
if command -v xdg-open &>/dev/null; then
    xdg-open "$URL" 2>/dev/null &
elif command -v open &>/dev/null; then
    open "$URL" 2>/dev/null &
else
    echo -e "${YELLOW}💡 请手动在浏览器中打开: ${URL}${NC}"
fi

# ── 保持脚本运行，等待 Ctrl+C ──────────────────────────────
wait
