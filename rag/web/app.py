
#!/usr/bin/env python3
"""
FastAPI web 应用 - 提供 RAG 问答 Web 界面
支持：Agent 架构 / Skills 管理 / SOP / 个人知识库

Agent 架构：LLM 驱动的工具调用循环替代固定 pipeline。
工具/技能按模式过滤：普通搜索 vs 深度调研 提供不同工具集。
"""
import sys
import logging
import asyncio
import json
import re
import shutil
import threading
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
# 添加项目根目录到路径（for admin blueprint）
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, Depends, Request, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.wsgi import WSGIMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from cachetools import TTLCache

# ---- 核心组件 ----
from core.llm_client import call_llm, call_llm_stream
from core.agent import Agent
from search.retriever import JinaRetriever as Retriever
from search.personal_lib import PersonalLibrary
from tools import Toolregistry
from tools.pubmed_search import PubmedSearchTool
from tools.gene_db_search import GeneDBSearchTool
from tools.personal_lib_search import PersonalLibSearchTool
from tools.rag_search import RAGSearchTool
from tools.crispr_tool import CrisprTool
from tools.read import Readtool
from tools.write import Writetool
from tools.shell import Shelltool
from skills.skill_loader import Skill_loader
from search.reranker import JinaReranker
import core.config as config

# 登录 & 管理
from web.auth import (
    get_current_user,
    user_profile_view,
    update_profile_view,
    delete_account_view,
    signup_with_email,
    verify_email_code,
    resend_verification_code,
)

# ------------------------------------------------------------------
# 日志初始化
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    force=True,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# FastAPI app
# ------------------------------------------------------------------
app = FastAPI(title="NutriMaster RAG", docs_url=None, redoc_url=None)

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.SITE_URL] if config.SITE_URL else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Rate Limiter ----
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse({"error": "请求频率过高，请稍后再试"}, status_code=429)


# ---- Upload size limit middleware (50 MB) ----
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_UPLOAD_BYTES:
                return JSONResponse({"error": "文件过大，最大 50MB"}, status_code=413)
        except ValueError:
            pass
    return await call_next(request)


# ---- Generic 500 handler ----
@app.exception_handler(Exception)
async def _generic_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        raise exc
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse({"error": "服务器内部错误，请稍后再试"}, status_code=500)


# ------------------------------------------------------------------
# 全局初始化
# ------------------------------------------------------------------
logger.info("开始初始化系统组件...")

# ---- 检索器（gene_db_search 依赖） ----
logger.info("初始化检索器...")
retriever = Retriever()
retriever.build_index()
logger.info(f"检索器初始化完成，已加载 {len(retriever.chunks)} 个文档块")

# ---- 个人库实例缓存 ----
_personal_libs: TTLCache = TTLCache(maxsize=200, ttl=3600)
_personal_libs_lock = threading.Lock()


def _get_personal_lib(user_id: str) -> PersonalLibrary:
    """获取用户个人库实例（懒加载，线程安全）"""
    with _personal_libs_lock:
        if user_id not in _personal_libs:
            _personal_libs[user_id] = PersonalLibrary(user_id)
        return _personal_libs[user_id]


def _get_personal_lib_for_user(user) -> PersonalLibrary:
    """兼容旧接口：接受 user 对象"""
    return _get_personal_lib(user.id)


# ---- Toolregistry：注册所有工具 ----
registry = Toolregistry()
pubmed_tool = PubmedSearchTool()
personal_tool = PersonalLibSearchTool(
    get_personal_lib=_get_personal_lib,
    get_query_embedding=retriever.get_query_embedding,
)
reranker = JinaReranker()
rag_search_tool = RAGSearchTool(
    pubmed_tool=pubmed_tool,
    retriever=retriever,
    reranker=reranker,
    get_personal_lib=_get_personal_lib,
    get_query_embedding=retriever.get_query_embedding,
)

registry.register(pubmed_tool)                              # PubMed（单独搜索）
registry.register(GeneDBSearchTool(retriever))              # 基因数据库（单独搜索）
registry.register(personal_tool)                            # 个人知识库（单独搜索）
registry.register(rag_search_tool)                          # RAG 综合搜索+重排
registry.register(CrisprTool())                             # CRISPR 实验方案
registry.register(Readtool())                               # 读文件
registry.register(Writetool())                              # 写文件
registry.register(Shelltool())                              # Shell 命令
logger.info(f"已注册 {len(registry.tool_names)} 个工具: {sorted(registry.tool_names)}")

# ---- Skill_loader ----
skill_loader = Skill_loader()
logger.info(f"已加载 Skills: {[s.name for s in skill_loader.list_dir()]}")

# ---- Agent ----
agent = Agent(
    registry=registry,
    skill_loader=skill_loader,
    call_llm=call_llm,
    call_llm_stream=call_llm_stream,
)

logger.info("系统初始化完成，所有组件就绪！")


# ------------------------------------------------------------------
# 工具函数
# ------------------------------------------------------------------

def _sse(payload: dict) -> str:
    """序列化 SSE 事件。"""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


_SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


# ------------------------------------------------------------------
# 静态文件 & 首页
# ------------------------------------------------------------------
_static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/")
async def index():
    """首页"""
    return FileResponse(str(_static_dir / "index.html"))


# ------------------------------------------------------------------
# 统一查询接口（Agent 架构）
# ------------------------------------------------------------------

@app.post("/api/query")
@limiter.limit("10/minute")
async def query(request: Request, user=Depends(get_current_user)):
    """处理查询请求 - SSE 流式输出（Agent 架构）"""
    data = await request.json()
    query_text = (data.get("query") or "").strip()
    logger.info(f"[/api/query] 收到查询请求: {query_text[:100]}...")
    if not query_text:
        raise HTTPException(status_code=400, detail="查询不能为空")

    # 为当前请求启动 Agent（user_id 通过 execute 参数传递，无需注入类属性）

    async def generate():
        try:
            async for event in agent.run(
                user_input=query_text,
                user_id=user.id,
                model_id=data.get("model_id", ""),
                history=data.get("history", []),
                use_personal=data.get("use_personal", False),
                use_depth=data.get("use_depth", False),
                skill_prefs=data.get("skill_prefs", {}),
                tool_overrides=data.get("tool_overrides", {}),
            ):
                yield _sse(event)
            logger.info(f"[/api/query] 查询完成: {query_text[:50]}...")
        except Exception as e:
            logger.exception(f"[/api/query] 查询异常: {query_text[:50]}...")
            yield _sse({"type": "error", "data": str(e)})

    return StreamingResponse(generate(), media_type="text/event-stream", headers=_SSE_HEADERS)


# ------------------------------------------------------------------
# SOP 接口（CRISPR 实验 — 独立于 skill/tool 系统）
# ------------------------------------------------------------------

@app.post("/api/sop/extract")
@limiter.limit("10/minute")
async def sop_extract_genes(request: Request, user=Depends(get_current_user)):
    """Phase A+B: 从对话中提取基因 → NCBI 验证。SSE 流式返回。"""
    data = await request.json()
    answer_text = (data.get("answer_text") or "").strip()
    query_text = (data.get("query") or "").strip()

    if not answer_text and not query_text:
        raise HTTPException(status_code=400, detail="缺少 answer_text 或 query")

    async def generate():
        from skills.crispr_experiment.pipeline import ExperimentPipeline
        from skills.crispr_experiment.gene2accession import (
            _search_gene_ids, _normalize_species_name,
        )
        from Bio import Entrez

        exp_pipeline = ExperimentPipeline()
        try:
            # Phase A: LLM 提取基因
            yield _sse({"type": "sop_extracting", "data": "正在从对话中提取基因..."})
            source_text = f"{query_text}\n{answer_text}".strip()
            genes = await asyncio.to_thread(exp_pipeline.extract_genes_with_llm, source_text)
            yield _sse({"type": "sop_genes_extracted", "genes": genes})

            # Phase B: NCBI 验证每个基因
            yield _sse({"type": "sop_ncbi_verifying", "data": "正在 NCBI 确认基因信息..."})
            Entrez.email = "biojson_rag@example.com"
            verified = []
            for g in genes:
                species = await asyncio.to_thread(_normalize_species_name, g.get("species", ""))
                gene_ids = await asyncio.to_thread(_search_gene_ids, g["gene"], species)
                verified.append({
                    "gene": g["gene"],
                    "species": g.get("species", ""),
                    "ncbi_found": len(gene_ids) > 0,
                    "gene_ids": gene_ids[:3],
                })
                await asyncio.sleep(0.34)  # NCBI rate limit
            yield _sse({"type": "sop_ncbi_verified", "genes": verified})

        except Exception as e:
            logger.exception("[/api/sop/extract] 基因提取/验证异常")
            yield _sse({"type": "error", "data": str(e)})
        finally:
            exp_pipeline.cleanup()

    return StreamingResponse(generate(), media_type="text/event-stream", headers=_SSE_HEADERS)


@app.post("/api/sop/run")
@limiter.limit("10/minute")
async def sop_run_pipeline(request: Request, user=Depends(get_current_user)):
    """Phase C: 用户确认基因后，执行完整 CRISPR 实验 pipeline。"""
    data = await request.json()
    genes = data.get("genes")
    if not genes:
        raise HTTPException(status_code=400, detail="缺少 genes 列表")

    logger.info(f"[/api/sop/run] 执行 SOP pipeline, genes={[g.get('gene') for g in genes]}")

    _SENTINEL = object()

    async def generate():
        from skills.crispr_experiment.pipeline import ExperimentPipeline

        exp_pipeline = ExperimentPipeline()
        try:
            # run_all_from_genes 是同步 generator，用 to_thread 迭代
            gen = exp_pipeline.run_all_from_genes(genes)
            while True:
                event = await asyncio.to_thread(next, gen, _SENTINEL)
                if event is _SENTINEL:
                    break
                yield _sse(event)
            yield _sse({"type": "done"})
            logger.info("[/api/sop/run] SOP pipeline 完成")
        except Exception as e:
            logger.exception("[/api/sop/run] SOP pipeline 异常")
            yield _sse({"type": "error", "data": str(e)})
        finally:
            exp_pipeline.cleanup()

    return StreamingResponse(generate(), media_type="text/event-stream", headers=_SSE_HEADERS)


# ------------------------------------------------------------------
# Skills 管理接口
# ------------------------------------------------------------------

@app.get("/api/skills")
async def list_skills(user=Depends(get_current_user)):
    """列出共享 + 用户私有 skills"""
    skills = skill_loader.list_dir(user_id=user.id)
    return JSONResponse({
        "skills": [
            {
                "name": s.name,
                "description": s.description,
                "tools": s.tools,
                "is_shared": s.is_shared,
                "content": s.content,
            }
            for s in skills
        ]
    })


@app.post("/api/skills/generate")
@limiter.limit("5/minute")
async def generate_skill(request: Request, user=Depends(get_current_user)):
    """用 LLM 根据用户描述生成 skill 初稿"""
    data = await request.json()
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        raise HTTPException(400, detail="请描述你想要的 Skill")

    # 构造 system prompt，包含可用 tools 列表和 skill 格式说明
    tools_info = "\n".join(f"- {t['name']}: {t['description']}" for t in registry.list_all())
    system = f"""你是一个 Skill 生成器。根据用户的描述，生成一个结构化的 Skill 定义。

可用的 Tools:
{tools_info}

请严格按以下 JSON 格式输出（不要输出其他内容）：
{{"name": "skill-name", "description": "一句话描述", "tools": ["tool1", "tool2"], "content": "Skill 的详细执行指令"}}

name 用小写字母+连字符。tools 只能从上面的可用 Tools 中选择。content 写清执行步骤。"""

    resp = await call_llm(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    text = resp.content.strip()
    # 解析 JSON
    try:
        result = json.loads(text)
    except Exception:
        # 尝试提取 JSON 块
        m = re.search(r'\{.*\}', text, re.DOTALL)
        result = json.loads(m.group()) if m else {"name": "", "description": "", "tools": [], "content": text}

    return JSONResponse(result)


@app.get("/api/skills/{name}")
async def get_skill(name: str, user=Depends(get_current_user)):
    """获取 skill 详情"""
    skill = skill_loader.get_skill(name, user_id=user.id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill 不存在")
    return JSONResponse({
        "name": skill.name,
        "description": skill.description,
        "tools": skill.tools,
        "content": skill.content,
        "is_shared": skill.is_shared,
    })


@app.post("/api/skills")
async def create_skill(request: Request, user=Depends(get_current_user)):
    """创建新 skill（用户私有）— 接受结构化字段"""
    data = await request.json()
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    tools = data.get("tools", [])
    content = (data.get("content") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name 不能为空")

    # 组装 frontmatter
    tools_str = ", ".join(tools) if tools else ""
    full_content = f"---\nname: {name}\ndescription: >\n  {description}\ntools: [{tools_str}]\n---\n\n{content}\n"

    spec = skill_loader.save_skill(name=name, content=full_content, user_id=user.id)
    return JSONResponse({
        "name": spec.name,
        "description": spec.description,
        "tools": spec.tools,
        "content": spec.content,
        "is_shared": spec.is_shared,
    })


@app.put("/api/skills/{name}")
async def update_skill(name: str, request: Request, user=Depends(get_current_user)):
    """更新 skill — 接受结构化字段"""
    data = await request.json()
    new_name = (data.get("name") or name).strip()
    description = (data.get("description") or "").strip()
    tools = data.get("tools", [])
    content = (data.get("content") or "").strip()

    # 只允许更新用户私有 skill
    existing = skill_loader.get_skill(name, user_id=user.id)
    if existing and existing.is_shared:
        raise HTTPException(status_code=403, detail="不允许修改共享 Skill")

    # 组装 frontmatter
    tools_str = ", ".join(tools) if tools else ""
    full_content = f"---\nname: {new_name}\ndescription: >\n  {description}\ntools: [{tools_str}]\n---\n\n{content}\n"

    spec = skill_loader.save_skill(name=name, content=full_content, user_id=user.id)
    return JSONResponse({
        "name": spec.name,
        "description": spec.description,
        "tools": spec.tools,
        "content": spec.content,
        "is_shared": spec.is_shared,
    })


@app.delete("/api/skills/{name}")
async def delete_skill(name: str, user=Depends(get_current_user)):
    """删除用户私有 skill"""
    ok = skill_loader.delete_skill(name=name, user_id=user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Skill 不存在或不允许删除")
    return JSONResponse({"status": "ok"})


# ------------------------------------------------------------------
# Tools 列表接口
# ------------------------------------------------------------------

@app.get("/api/tools")
async def list_tools(user=Depends(get_current_user)):
    """列出已注册的 tool（name + description）"""
    return JSONResponse({"tools": registry.list_all()})


# ------------------------------------------------------------------
# FileStorage 适配器 (UploadFile → Flask-like .save())
# ------------------------------------------------------------------

class FileStorageAdapter:
    """让 FastAPI UploadFile 提供 Flask FileStorage 兼容的 .save() 方法"""
    def __init__(self, upload_file: UploadFile):
        self._f = upload_file

    def save(self, path):
        with open(path, "wb") as out:
            shutil.copyfileobj(self._f.file, out)


# ------------------------------------------------------------------
# 个人知识库接口
# ------------------------------------------------------------------

@app.post("/api/personal/upload")
@limiter.limit("5/minute")
async def personal_upload(request: Request, file: UploadFile = File(...), user=Depends(get_current_user)):
    """上传 PDF 到个人库"""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件")

    try:
        adapter = FileStorageAdapter(file)
        lib = _get_personal_lib_for_user(user)
        info = await asyncio.to_thread(lib.upload_pdf, adapter, file.filename)
        return JSONResponse({"status": "ok", "file": info})
    except (ValueError, ImportError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Upload failed")
        return JSONResponse({"error": "上传失败，请稍后再试"}, status_code=500)


@app.get("/api/personal/files")
async def personal_files(user=Depends(get_current_user)):
    """列出个人库文件"""
    lib = _get_personal_lib_for_user(user)
    files = await asyncio.to_thread(lib.list_files)
    return JSONResponse({"files": files})


@app.delete("/api/personal/files/{filename}")
async def personal_delete(filename: str, user=Depends(get_current_user)):
    """删除个人库文件"""
    lib = _get_personal_lib_for_user(user)
    ok = await asyncio.to_thread(lib.delete_file, filename)
    if ok:
        return JSONResponse({"status": "ok"})
    raise HTTPException(status_code=404, detail="文件不存在")


@app.put("/api/personal/files/{filename}/rename")
async def personal_rename(filename: str, request: Request, user=Depends(get_current_user)):
    """重命名个人库文件"""
    data = await request.json()
    new_name = (data.get("new_name") or "").strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="新文件名不能为空")

    lib = _get_personal_lib_for_user(user)
    ok = await asyncio.to_thread(lib.rename_file, filename, new_name)
    if ok:
        return JSONResponse({"status": "ok"})
    raise HTTPException(status_code=404, detail="文件不存在")


# ------------------------------------------------------------------
# 认证接口（注册 / 验证码）
# ------------------------------------------------------------------

@app.post("/api/auth/signup")
@limiter.limit("5/minute")
async def auth_signup(request: Request):
    """注册新用户并发送验证码"""
    return await signup_with_email(request)


@app.post("/api/auth/verify")
@limiter.limit("10/minute")
async def auth_verify(request: Request):
    """验证邮箱验证码"""
    return await verify_email_code(request)


@app.post("/api/auth/resend")
@limiter.limit("3/minute")
async def auth_resend(request: Request):
    """重新发送验证码"""
    return await resend_verification_code(request)


# ------------------------------------------------------------------
# 用户信息接口
# ------------------------------------------------------------------

@app.get("/api/user/profile")
async def user_profile(user=Depends(get_current_user)):
    return await user_profile_view(user=user)


@app.put("/api/user/profile")
async def user_profile_update(request: Request, user=Depends(get_current_user)):
    return await update_profile_view(request=request, user=user)


@app.delete("/api/user/account")
async def user_account_delete(user=Depends(get_current_user)):
    return await delete_account_view(user=user)


# ------------------------------------------------------------------
# 其他接口
# ------------------------------------------------------------------

@app.get("/api/health")
async def health():
    """健康检查"""
    return JSONResponse({
        "status": "ok",
        "total_chunks": len(retriever.chunks),
    })


@app.get("/api/config")
async def frontend_config():
    """返回前端需要的公开配置（Supabase + 可用模型列表）"""
    return JSONResponse({
        "supabase_url": config.SUPABASE_URL,
        "supabase_anon_key": config.SUPABASE_ANON_KEY,
        "admin_port": config.ADMIN_PORT,
        "site_url": config.SITE_URL,
        "models": [
            {"id": m["id"], "name": m["name"]}
            for m in config.MODEL_OPTIONS
        ],
    })


# ------------------------------------------------------------------
# Admin Blueprint 挂载（通过 WSGIMiddleware 零修改集成）
# ------------------------------------------------------------------
from flask import Flask as FlaskApp
from admin.app import admin_bp

_admin_flask = FlaskApp(__name__, static_folder=None)
_admin_flask.register_blueprint(admin_bp)
app.mount("/admin", WSGIMiddleware(_admin_flask))


# ------------------------------------------------------------------
# 开发模式直接运行
# ------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    logger.info(f"启动 uvicorn 服务: {config.WEB_HOST}:{config.WEB_PORT}, debug={config.DEBUG}")
    uvicorn.run(
        "app:app",
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        reload=config.DEBUG,
    )
