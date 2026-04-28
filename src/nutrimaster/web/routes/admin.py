from __future__ import annotations

import json
import logging
import threading
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from nutrimaster.auth.service import ADMIN_EMAILS, get_current_user
from nutrimaster.web.deps import WebServices, get_services

logger = logging.getLogger(__name__)
router = APIRouter()


def _require_admin(user) -> None:
    email = (user.email or "").lower()
    if email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="仅管理员可访问")


@router.get("/api/skills")
async def list_skills(user=Depends(get_current_user), services: WebServices = Depends(get_services)):
    skills = services.skill_loader.list_dir()
    return JSONResponse(
        {
            "skills": [
                {
                    "name": skill.name,
                    "description": skill.description,
                    "tools": skill.tools,
                    "is_shared": skill.is_shared,
                    "content": skill.content,
                }
                for skill in skills
            ]
        }
    )


@router.get("/api/skills/{name}")
async def get_skill(name: str, user=Depends(get_current_user), services: WebServices = Depends(get_services)):
    skill = services.skill_loader.get_skill(name)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill 不存在")
    return JSONResponse(
        {
            "name": skill.name,
            "description": skill.description,
            "tools": skill.tools,
            "content": skill.content,
            "is_shared": skill.is_shared,
        }
    )


@router.post("/api/skills")
@router.post("/api/skills/generate")
@router.put("/api/skills/{name}")
@router.delete("/api/skills/{name}")
async def skills_readonly():
    raise HTTPException(status_code=410, detail="Skills 现在通过后台文件夹维护，不再提供前端编辑接口")


@router.get("/api/tools")
async def list_tools(user=Depends(get_current_user), services: WebServices = Depends(get_services)):
    return JSONResponse({"tools": services.registry.list_all()})


def _background_reindex(services: WebServices) -> None:
    state = services.reindex_state
    try:
        with state.lock:
            state.running = True
            state.progress = "开始增量重索引..."
            state.error = None
        services.refresh_index(force=False)
        with state.lock:
            state.running = False
            state.progress = f"完成！当前索引: {len(services.retriever.chunks)} chunks"
            state.last_completed = datetime.now().isoformat()
    except Exception as exc:
        logger.exception("[admin] reindex failed")
        with state.lock:
            state.running = False
            state.error = str(exc)
            state.progress = "重索引失败"


@router.post("/api/admin/upload_data")
async def admin_upload_data(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    services: WebServices = Depends(get_services),
):
    _require_admin(user)
    filename = file.filename or ""
    if not filename.endswith("_nutri_plant_verified.json"):
        raise HTTPException(status_code=400, detail="文件名必须以 _nutri_plant_verified.json 结尾")
    if services.settings.rag is None:
        raise HTTPException(status_code=500, detail="RAG 未配置")
    target_path = services.settings.rag.data_dir / filename
    try:
        content = await file.read()
        json.loads(content.decode("utf-8"))
        target_path.write_bytes(content)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="文件不是有效的 JSON 格式") from exc

    state = services.reindex_state
    with state.lock:
        if state.running:
            return JSONResponse({"status": "queued", "filename": filename})
    threading.Thread(target=_background_reindex, args=(services,), daemon=True).start()
    return JSONResponse({"status": "ok", "filename": filename})


@router.get("/api/admin/reindex_status")
async def admin_reindex_status(
    user=Depends(get_current_user),
    services: WebServices = Depends(get_services),
):
    _require_admin(user)
    state = services.reindex_state
    data_files_count = 0
    if services.settings.rag is not None:
        data_files_count = len(list(services.settings.rag.data_dir.glob("*_nutri_plant_verified.json")))
    with state.lock:
        payload = {
            "running": state.running,
            "progress": state.progress,
            "error": state.error,
            "last_completed": state.last_completed,
            "current_chunks": len(services.retriever.chunks),
            "data_files_count": data_files_count,
        }
    return JSONResponse(payload)
