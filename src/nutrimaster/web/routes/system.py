from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from nutrimaster.web.deps import WebServices, get_services

router = APIRouter()


@router.get("/api/health")
async def health(services: WebServices = Depends(get_services)):
    index_status = services.retriever.index_status() if hasattr(services.retriever, "index_status") else {}
    return JSONResponse(
        {
            "status": "ok",
            "total_chunks": len(services.retriever.chunks),
            "index": index_status,
            "tools": sorted(services.registry.tool_names),
            "skills": [skill.name for skill in services.skill_loader.list_dir()],
        }
    )


@router.get("/api/config")
async def frontend_config(services: WebServices = Depends(get_services)):
    settings = services.settings
    rag = settings.rag
    return JSONResponse(
        {
            "supabase_url": settings.supabase_url,
            "supabase_anon_key": settings.supabase_anon_key,
            "admin_port": rag.admin_port if rag else 5501,
            "site_url": settings.site_url,
            "models": [],
            "interaction_capture": services.interaction_recorder.policy.public_config(),
        }
    )
