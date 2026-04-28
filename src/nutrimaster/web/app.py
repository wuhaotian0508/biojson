
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
import os
import re
import shutil
import threading
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Depends, Request, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.wsgi import WSGIMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from cachetools import TTLCache

from nutrimaster.agent.stack import build_agent_stack
from nutrimaster.rag.jina_retriever import JinaRetriever
from nutrimaster.rag.personal_library import PersonalLibrary
from nutrimaster.agent.tools.retrieval import PersonalLibSearchTool
from nutrimaster.config.settings import Settings

# 登录 & 管理
from nutrimaster.auth.service import (
    get_current_user,
    user_profile_view,
    update_profile_view,
    delete_account_view,
    signup_with_email,
    verify_email_code,
    resend_verification_code,
    ADMIN_EMAILS,
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
_SETTINGS = Settings.from_env()
if _SETTINGS.rag is None:
    raise RuntimeError("RAG settings failed to initialize")
_RAG_SETTINGS = _SETTINGS.rag

# ------------------------------------------------------------------
# FastAPI app
# ------------------------------------------------------------------
app = FastAPI(title="NutriMaster RAG", docs_url=None, redoc_url=None)

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_SETTINGS.site_url] if _SETTINGS.site_url else ["*"],
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

# ---- 个人库实例缓存 ----
_personal_libs: TTLCache = TTLCache(maxsize=200, ttl=3600)
_personal_libs_lock = threading.Lock()

# ---- 后台重索引状态管理 ----
_reindex_lock = threading.Lock()
_reindex_state = {
    "running": False,
    "progress": "",
    "error": None,
    "last_completed": None,
}


def _get_personal_lib(user_id: str) -> PersonalLibrary:
    """获取用户个人库实例（懒加载，线程安全）"""
    with _personal_libs_lock:
        if user_id not in _personal_libs:
            _personal_libs[user_id] = PersonalLibrary(user_id)
        return _personal_libs[user_id]


def _get_personal_lib_for_user(user) -> PersonalLibrary:
    """兼容旧接口：接受 user 对象"""
    return _get_personal_lib(user.id)


# ---- Agent stack ----
logger.info("初始化 Agent stack...")
retriever = JinaRetriever()
build_index_on_startup = os.getenv("NUTRIMASTER_WEB_BUILD_INDEX", "").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
stack = build_agent_stack(
    retriever=retriever,
    build_index=build_index_on_startup,
    personal_lib_tool_factory=lambda: PersonalLibSearchTool(
        get_personal_lib=_get_personal_lib,
        get_query_embedding=retriever.get_query_embedding,
    ),
)
registry = stack.registry
skill_loader = stack.skill_loader
agent = stack.agent_runtime.agent
logger.info(f"已注册 {len(registry.tool_names)} 个工具: {sorted(registry.tool_names)}")
logger.info(f"已加载 Skills: {[s.name for s in skill_loader.list_dir()]}")
logger.info(f"检索器初始化完成，已加载 {len(retriever.chunks)} 个文档块")

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
    user_genes = data.get("user_genes") or []  # 用户在前端编辑器中选择/添加的基因

    if not answer_text and not query_text and not user_genes:
        raise HTTPException(status_code=400, detail="缺少 answer_text、query 或 user_genes")

    async def generate():
        from nutrimaster.crispr.pipeline import ExperimentPipeline
        from nutrimaster.crispr.gene2accession import (
            _search_gene_ids, _normalize_species_name,
        )
        from Bio import Entrez

        exp_pipeline = ExperimentPipeline()
        try:
            # Phase A: 提取基因（优先使用用户提供的基因列表）
            if user_genes:
                # 用户已在前端编辑器中选择/添加基因，使用 LLM 为这些基因解析物种
                yield _sse({"type": "sop_extracting", "data": f"正在为 {len(user_genes)} 个基因解析物种信息..."})
                source_text = f"{query_text}\n{answer_text}".strip()
                genes = await asyncio.to_thread(
                    exp_pipeline.extract_selected_genes_with_llm,
                    source_text,
                    user_genes
                )
            else:
                # 用户未提供基因列表，从对话中自动提取
                yield _sse({"type": "sop_extracting", "data": "正在从对话中提取基因..."})
                source_text = f"{query_text}\n{answer_text}".strip()
                genes = await asyncio.to_thread(exp_pipeline.extract_genes_with_llm, source_text)
            yield _sse({"type": "sop_genes_extracted", "genes": genes})

            # Phase B: NCBI 验证每个基因
            yield _sse({"type": "sop_ncbi_verifying", "data": "正在 NCBI 确认基因信息..."})
            Entrez.email = "nutrimaster_rag@example.com"
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
        from nutrimaster.crispr.pipeline import ExperimentPipeline

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
# 管理员接口（数据上传 + 重索引）
# ------------------------------------------------------------------

def _background_reindex():
    """后台线程执行增量重索引"""
    global _reindex_state
    try:
        with _reindex_lock:
            _reindex_state["running"] = True
            _reindex_state["progress"] = "开始增量重索引..."
            _reindex_state["error"] = None

        logger.info("[admin] 开始后台增量重索引")
        _reindex_state["progress"] = "正在扫描新增/修改文件..."

        # 触发增量构建
        retriever.build_index(incremental=True, force=False)

        _reindex_state["progress"] = "索引构建完成，清理 BM25 缓存..."
        # 清理 BM25 缓存，强制下次 hybrid_search 时重建
        retriever._bm25 = None

        with _reindex_lock:
            _reindex_state["running"] = False
            _reindex_state["progress"] = f"完成！当前索引: {len(retriever.chunks)} chunks"
            _reindex_state["last_completed"] = datetime.now().isoformat()

        logger.info(f"[admin] 重索引完成，当前 {len(retriever.chunks)} chunks")

    except Exception as e:
        logger.exception("[admin] 重索引失败")
        with _reindex_lock:
            _reindex_state["running"] = False
            _reindex_state["error"] = str(e)
            _reindex_state["progress"] = "重索引失败"


@app.post("/api/admin/upload_data")
async def admin_upload_data(
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    """
    管理员上传 *_nutri_plant_verified.json 文件到 DATA_DIR 并触发增量重索引。

    要求：
      - 用户必须是管理员（is_admin=True）
      - 文件名必须符合 *_nutri_plant_verified.json 格式
      - 文件大小不超过 50MB（由全局中间件限制）
    """
    # 权限检查
    email = (user.email or "").lower()
    if email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="仅管理员可上传数据文件")

    # 文件名校验
    filename = file.filename or ""
    if not filename.endswith("_nutri_plant_verified.json"):
        raise HTTPException(
            status_code=400,
            detail="文件名必须以 _nutri_plant_verified.json 结尾"
        )

    # 保存文件到 DATA_DIR
    target_path = _RAG_SETTINGS.data_dir / filename
    try:
        content = await file.read()
        # 验证是否为有效 JSON
        json.loads(content.decode("utf-8"))

        # 原子写入
        target_path.write_bytes(content)
        logger.info(f"[admin] 已保存文件: {target_path}")

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="文件不是有效的 JSON 格式")
    except Exception as e:
        logger.exception("[admin] 保存文件失败")
        raise HTTPException(status_code=500, detail=f"保存失败: {e}")

    # 检查是否已有重索引任务在运行
    with _reindex_lock:
        if _reindex_state["running"]:
            return JSONResponse({
                "status": "queued",
                "message": "文件已保存，但重索引任务正在运行中，请稍后查看状态",
                "filename": filename,
            })

    # 启动后台重索引线程
    threading.Thread(target=_background_reindex, daemon=True).start()

    return JSONResponse({
        "status": "ok",
        "message": "文件已保存，后台重索引已启动",
        "filename": filename,
    })


@app.get("/api/admin/reindex_status")
async def admin_reindex_status(user=Depends(get_current_user)):
    """
    查询当前索引状态和后台重索引进度。

    返回：
      - running: 是否正在重索引
      - progress: 当前进度描述
      - error: 错误信息（如有）
      - last_completed: 上次完成时间（ISO 格式）
      - current_chunks: 当前索引的 chunk 数量
      - data_files: DATA_DIR 中的文件数量
    """
    # 权限检查
    email = (user.email or "").lower()
    if email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="仅管理员可查看索引状态")

    # 统计 DATA_DIR 中的文件数
    data_files = list(_RAG_SETTINGS.data_dir.glob("*_nutri_plant_verified.json"))

    with _reindex_lock:
        state = dict(_reindex_state)

    return JSONResponse({
        "running": state["running"],
        "progress": state["progress"],
        "error": state["error"],
        "last_completed": state["last_completed"],
        "current_chunks": len(retriever.chunks),
        "data_files_count": len(data_files),
    })


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
    index_status = retriever.index_status() if hasattr(retriever, "index_status") else {}
    return JSONResponse({
        "status": "ok",
        "total_chunks": len(retriever.chunks),
        "index": index_status,
    })


@app.get("/api/config")
async def frontend_config():
    """返回前端需要的公开配置（Supabase，不再暴露模型列表）"""
    return JSONResponse({
        "supabase_url": _SETTINGS.supabase_url,
        "supabase_anon_key": _SETTINGS.supabase_anon_key,
        "admin_port": _RAG_SETTINGS.admin_port,
        "site_url": _SETTINGS.site_url,
        "models": [],  # 不再对外展示模型选择
    })


# ------------------------------------------------------------------
# Admin Blueprint 挂载（通过 WSGIMiddleware 零修改集成）
# ------------------------------------------------------------------
from flask import Flask as FlaskApp
from nutrimaster.web.admin.app import admin_bp, configure_index_refresh


def _refresh_admin_index(data_dir: Path, force: bool = False) -> None:
    retriever.build_index(data_dir=data_dir, incremental=True, force=force)
    if hasattr(retriever, "_bm25"):
        retriever._bm25 = None


_admin_flask = FlaskApp(__name__, static_folder=None)
configure_index_refresh(_refresh_admin_index)
_admin_flask.register_blueprint(admin_bp)
app.mount("/admin", WSGIMiddleware(_admin_flask))


# ------------------------------------------------------------------
# 开发模式直接运行
# ------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    logger.info(
        f"启动 uvicorn 服务: {_RAG_SETTINGS.web_host}:{_RAG_SETTINGS.web_port}, "
        f"debug={_RAG_SETTINGS.debug}"
    )
    uvicorn.run(
        "nutrimaster.web.app:app",
        host=_RAG_SETTINGS.web_host,
        port=_RAG_SETTINGS.web_port,
        reload=_RAG_SETTINGS.debug,
    )
