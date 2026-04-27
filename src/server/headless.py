#!/usr/bin/env python3
"""
NutriMaster Headless RAG API Server - 用于 pipeline 测试的轻量级 API

提供核心功能：
  - POST /api/query - 同步查询（返回完整结果）
  - POST /api/query/stream - 流式查询（SSE）
  - GET /api/health - 健康检查
  - GET /api/tools - 列出可用工具

去除了 Web UI、认证、个人库等复杂功能，专注于核心 RAG 能力测试。
"""
import logging
import os

import uvicorn

from app.agent_stack import build_legacy_agent_stack
from retrieval.search_service import RetrievalService
from server.api import QueryRequest, QueryResponse, create_api_app

# 配置日志格式：时间戳 + 日志级别 + 模块名 + 消息
# 这样可以清晰追踪每个请求的处理流程
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# 全局初始化（模块加载时执行一次，避免每次请求重复初始化）
# ------------------------------------------------------------------
logger.info("初始化 RAG 组件...")
build_index_on_startup = os.getenv("NUTRIMASTER_API_BUILD_INDEX", "").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
stack = build_legacy_agent_stack(build_index=build_index_on_startup)
retriever = stack.retriever
registry = stack.registry
skill_loader = stack.skill_loader
agent_runtime = stack.agent_runtime
agent = stack.agent_runtime.legacy_agent
logger.info(f"检索器初始化完成，已加载 {len(retriever.chunks)} 个文档块")
logger.info(f"已注册工具: {list(registry.tool_names)}")
logger.info(f"已加载 {len(skill_loader.list_dir(None))} 个系统技能")
app = create_api_app(
    agent_runtime=agent_runtime,
    retrieval_service=RetrievalService(retriever=retriever),
    tool_names=registry.tool_names,
    skill_count=lambda: len(skill_loader.list_dir(None)),
    tools=registry._tools.values(),
)
logger.info("RAG API 初始化完成")


# ------------------------------------------------------------------
# 直接运行入口（python server.py）
# 生产环境建议用 start.sh 或 uvicorn 命令启动，而非直接运行此文件
# ------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NutriMaster Headless RAG API Server")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址（0.0.0.0 表示接受所有网卡）")
    parser.add_argument("--port", type=int, default=8000, help="监听端口")
    # --reload 会监听文件变化并自动重启，仅用于开发调试，生产环境不要开启
    parser.add_argument("--reload", action="store_true", help="开发模式（自动重载）")
    args = parser.parse_args()

    logger.info(f"启动 RAG API: {args.host}:{args.port}")
    # 以字符串形式传入 app 路径，这样 --reload 模式才能正确重载模块
    uvicorn.run(
        "server.headless:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
