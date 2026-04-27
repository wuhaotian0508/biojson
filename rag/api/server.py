#!/usr/bin/env python3
"""
RAG API Server - 用于 pipeline 测试的轻量级 API

提供核心功能：
  - POST /api/query - 同步查询（返回完整结果）
  - POST /api/query/stream - 流式查询（SSE）
  - GET /api/health - 健康检查
  - GET /api/tools - 列出可用工具

去除了 Web UI、认证、个人库等复杂功能，专注于核心 RAG 能力测试。
"""
import sys
import logging
import asyncio
from pathlib import Path
from typing import Optional

# 将项目根目录（biojson/）加入 Python 模块搜索路径，
# 使得 `from rag.xxx import ...` 这类绝对导入能正常工作。
# __file__ 是 api/server.py，parent.parent.parent 即 biojson/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

# 导入核心组件：
# - call_llm/call_llm_stream: 与 LLM 交互的底层函数
# - Agent: 负责工具调用和多轮对话的核心逻辑
# - Retriever: 文档检索器（基于 Jina Embeddings）
# - configure_query_translator: 配置查询翻译器的 LLM
# - configure_query_optimizer: 配置 PubMed 查询优化器的 LLM
# - Toolregistry: 工具注册中心，管理所有可用工具
# - 各种 Tool: PubMed 搜索、基因数据库、RAG 搜索、CRISPR 设计等
# - Skill_loader: 加载系统技能（预定义的复杂任务流程）
# - Reranker: 对检索结果进行重排序，提升相关性
from rag.core.llm_client import call_llm, call_llm_stream
from rag.core.agent import Agent
from rag.search.retriever import JinaRetriever as Retriever
from rag.search.query_translator import configure_llm as configure_query_translator
from rag.tools import Toolregistry
from rag.tools.pubmed_search import PubmedSearchTool, configure_query_optimizer
from rag.tools.pubmed_search import PubmedSearchTool
from rag.tools.gene_db_search import GeneDBSearchTool
from rag.tools.personal_lib_search import PersonalLibSearchTool
from rag.tools.rag_search import RAGSearchTool
from rag.tools.crispr_tool import CrisprTool
from rag.skills.skill_loader import Skill_loader
from rag.search.reranker import JinaReranker
import rag.core.config as config

# 配置日志格式：时间戳 + 日志级别 + 模块名 + 消息
# 这样可以清晰追踪每个请求的处理流程
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用实例
# 这是整个 API 服务的入口点
app = FastAPI(title="RAG API", version="1.0.0")

# ------------------------------------------------------------------
# 请求/响应模型
# ------------------------------------------------------------------
class QueryRequest(BaseModel):
    """
    查询请求的数据模型。
    使用 Pydantic 做自动校验，确保客户端传入的字段类型正确。
    """
    query: str = Field(..., description="用户查询文本")
    # primary 使用主力模型，fallback 在主力模型不可用时切换备用模型
    model_id: str = Field("primary", description="模型 ID (primary/fallback)")
    # 深度模式会触发更多轮工具调用，适合复杂问题，但耗时更长
    use_depth: bool = Field(False, description="是否启用深度模式")

    class Config:
        # 为 FastAPI 自动生成的 /docs 页面提供示例请求体
        json_schema_extra = {
            "example": {
                "query": "番茄中番茄红素合成的关键基因有哪些？",
                "model_id": "primary",
                "use_depth": False
            }
        }


class QueryResponse(BaseModel):
    """
    查询响应的数据模型。
    包含最终答案、引用来源和工具调用记录，方便调用方做进一步处理。
    """
    answer: str = Field(..., description="回答文本")
    sources: list[dict] = Field(default_factory=list, description="引用来源")
    # 记录 Agent 调用了哪些工具，便于调试和审计
    tool_calls: list[dict] = Field(default_factory=list, description="工具调用记录")
    steps: int = Field(..., description="实际执行步数")


# ------------------------------------------------------------------
# 全局初始化（模块加载时执行一次，避免每次请求重复初始化）
# ------------------------------------------------------------------
logger.info("初始化 RAG 组件...")

# 配置查询翻译器 LLM
logger.info("配置查询翻译器...")
configure_query_translator(
    api_key=config.LLM_API_KEY,
    base_url=config.LLM_BASE_URL,
    model="gpt-4o-mini",  # 使用快速小模型做术语提取
)

# 配置 PubMed 查询优化器
logger.info("配置 PubMed 查询优化器...")
configure_query_optimizer(
    api_key=config.LLM_API_KEY,
    base_url=config.LLM_BASE_URL,
    model="gpt-4o-mini",  # 使用快速小模型做查询优化
)

# 构建向量索引：将文档块转为 embedding 并存入内存
# build_index() 在启动时执行，避免首次请求时的延迟
retriever = Retriever()
retriever.build_index()
logger.info(f"检索器初始化完成，已加载 {len(retriever.chunks)} 个文档块")

# 初始化工具注册中心和各工具实例
registry = Toolregistry()
pubmed_tool = PubmedSearchTool()
gene_db_tool = GeneDBSearchTool(retriever=retriever)
# 测试环境不使用个人库：不传 callback，search_raw 会直接返回空列表
personal_lib_tool = PersonalLibSearchTool()
reranker = JinaReranker()

# RAGSearchTool 现在接收 `sources: dict[str, SearchSource]` + reranker:
# - "pubmed":       在线检索 PubMed 文献
# - "gene_db":      本地向量库检索(封装 retriever)
# - "personal_lib": 个人库检索壳(测试环境 search_raw 返回 [])
# - reranker:       对混合检索结果重排序
# 新增来源时只要往这个 dict 加一行即可,rag_search 本体零改动。
rag_search_tool = RAGSearchTool(
    sources={
        "pubmed": pubmed_tool,
        "gene_db": gene_db_tool,
        "personal_lib": personal_lib_tool,
    },
    reranker=reranker,
)

# 将所有工具注册到中心，Agent 运行时会从这里查找可用工具
registry.register(pubmed_tool)
registry.register(gene_db_tool)
registry.register(rag_search_tool)
registry.register(CrisprTool())

logger.info(f"已注册工具: {list(registry.tool_names)}")

# 只加载系统级 skills（list_dir(None) 表示不指定用户，返回系统技能列表）
skill_loader = Skill_loader()
logger.info(f"已加载 {len(skill_loader.list_dir(None))} 个系统技能")

# Agent 是整个 RAG pipeline 的调度核心：
# 接收用户输入 → 决策调用哪些工具 → 汇总结果 → 生成最终回答
agent = Agent(
    registry=registry,
    skill_loader=skill_loader,
    call_llm=call_llm,
    call_llm_stream=call_llm_stream,
)

logger.info("RAG API 初始化完成")


# ------------------------------------------------------------------
# API 端点定义
# ------------------------------------------------------------------
@app.get("/api/health")
async def health():
    """
    健康检查端点。
    返回系统状态概览，包括文档块数量、可用工具和技能数。
    用于部署后验证服务是否就绪，也可被负载均衡器用作存活探针。
    """
    return JSONResponse({
        "status": "ok",
        "total_chunks": len(retriever.chunks),
        "tools": list(registry.tool_names),
        "skills": len(skill_loader.list_dir(None)),
    })


@app.get("/api/tools")
async def list_tools():
    """
    列出所有已注册的工具及其描述。
    方便客户端了解当前系统支持哪些工具能力，
    也便于前端展示工具列表供用户参考。
    """
    return JSONResponse({
        "tools": [
            {"name": t.name, "description": t.description}
            for t in registry._tools.values()
        ]
    })


@app.post("/api/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """
    同步查询端点 - 等待 Agent 完成所有工具调用后返回完整结果。
    适合对延迟不敏感的批量测试场景。

    工作流程：
    1. 将查询发给 Agent
    2. Agent 异步迭代产生事件（text / tool_call / sources / error）
    3. 收集所有事件，拼装最终响应返回
    """
    try:
        answer_parts = []   # 收集文本片段，最后拼接成完整答案
        sources = []        # 引用来源列表
        tool_calls = []     # 工具调用记录
        steps = 0           # 工具调用计数器

        # agent.run() 是一个异步生成器，每轮工具调用/文本生成都会 yield 一个事件
        async for event in agent.run(
            user_input=req.query,  # 参数名是 user_input 不是 query
            user_id=None,  # 测试环境不需要用户 ID（无登录态）
            model_id=req.model_id,
            use_depth=req.use_depth,
            use_personal=False,  # 不使用个人库，避免测试时依赖用户数据
        ):
            event_type = event.get("type")

            if event_type == "text":
                # LLM 生成的文本片段，可能是流式到达的
                answer_parts.append(event.get("data", ""))

            elif event_type == "tool_call":
                # 每次 Agent 调用工具时触发，记录工具名和参数
                steps += 1
                tool_calls.append({
                    "tool": event.get("tool"),
                    "args": event.get("args"),
                })

            elif event_type == "sources":
                # 引用来源在所有工具调用完成后一次性返回
                sources = event.get("data", [])

            elif event_type == "error":
                # Agent 内部出错时抛出 HTTP 500，让客户端知道失败原因
                raise HTTPException(status_code=500, detail=event.get("data"))

        return QueryResponse(
            answer="".join(answer_parts),
            sources=sources,
            tool_calls=tool_calls,
            steps=steps,
        )

    except Exception as e:
        logger.exception("查询失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query/stream")
async def query_stream(req: QueryRequest):
    """
    流式查询端点 - 通过 Server-Sent Events (SSE) 实时推送事件。
    适合需要实时展示中间结果的场景（如前端逐字显示回答）。

    SSE 协议格式：每个事件以 "data: {json}\n\n" 格式发送，
    客户端用 EventSource API 或逐行解析即可。
    """
    async def event_generator():
        """
        内部异步生成器函数。
        将 Agent 产生的事件逐个转为 SSE 格式推送给客户端。
        使用 ensure_ascii=False 保证中文等 Unicode 字符不被转义。
        """
        try:
            async for event in agent.run(
                user_input=req.query,  # 参数名是 user_input 不是 query
                user_id=None,
                model_id=req.model_id,
                use_depth=req.use_depth,
                use_personal=False,
            ):
                # SSE 格式要求：每条数据以 "data: " 开头，以两个换行结尾
                import json
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        except Exception as e:
            # 流式传输中出错也要通过 SSE 通道告知客户端，
            # 因为此时 HTTP 状态码已经发出（200），无法再改为 500
            logger.exception("流式查询失败")
            import json
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)}, ensure_ascii=False)}\n\n"

    # 返回 StreamingResponse，media_type 设为 SSE 标准类型
    # Cache-Control: no-cache 防止代理缓存流式数据
    # Connection: keep-alive 保持长连接不被中断
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# ------------------------------------------------------------------
# 直接运行入口（python server.py）
# 生产环境建议用 start.sh 或 uvicorn 命令启动，而非直接运行此文件
# ------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RAG API Server")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址（0.0.0.0 表示接受所有网卡）")
    parser.add_argument("--port", type=int, default=8000, help="监听端口")
    # --reload 会监听文件变化并自动重启，仅用于开发调试，生产环境不要开启
    parser.add_argument("--reload", action="store_true", help="开发模式（自动重载）")
    args = parser.parse_args()

    logger.info(f"启动 RAG API: {args.host}:{args.port}")
    # 以字符串形式传入 app 路径，这样 --reload 模式才能正确重载模块
    uvicorn.run(
        "api.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
