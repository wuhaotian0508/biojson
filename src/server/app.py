from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from server.deps import EmptyRetrievalService
from shared.settings import Settings


_EmptyRetrievalService = EmptyRetrievalService


def create_app(
    *,
    settings: Settings | None = None,
    retrieval_service: Any | None = None,
    agent_runtime: Any | None = None,
) -> FastAPI:
    """Create a NutriMaster FastAPI app with explicit dependencies."""

    settings = settings or Settings.from_env()
    retrieval_service = retrieval_service or _EmptyRetrievalService()

    app = FastAPI(title="NutriMaster RAG", docs_url=None, redoc_url=None)

    @app.get("/api/health")
    async def health():
        return JSONResponse(
            {
                "status": "ok",
                "total_chunks": retrieval_service.total_chunks,
            }
        )

    @app.get("/api/config")
    async def frontend_config():
        return JSONResponse(
            {
                "supabase_url": settings.supabase_url,
                "supabase_anon_key": settings.supabase_anon_key,
                "admin_port": settings.rag.admin_port if settings.rag else 5501,
                "site_url": settings.site_url,
                "models": [],
            }
        )

    @app.post("/api/query")
    async def query(request: Request):
        data = await request.json()
        query_text = (data.get("query") or "").strip()
        if not query_text:
            raise HTTPException(status_code=400, detail="查询不能为空")
        if agent_runtime is None:
            raise HTTPException(status_code=503, detail="Agent runtime is not configured")

        async def generate():
            async for event in agent_runtime.run(
                user_input=query_text,
                user_id=None,
                model_id=data.get("model_id", ""),
                history=data.get("history", []),
                use_personal=data.get("use_personal", False),
                use_depth=data.get("use_depth", False),
                skill_prefs=data.get("skill_prefs", {}),
                tool_overrides=data.get("tool_overrides", {}),
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return app
