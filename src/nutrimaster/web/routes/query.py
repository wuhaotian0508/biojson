from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from nutrimaster.auth.service import get_current_user
from nutrimaster.web.deps import SSE_HEADERS, WebServices, get_services, sse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/query")
async def query(
    request: Request,
    user=Depends(get_current_user),
    services: WebServices = Depends(get_services),
):
    data = await request.json()
    query_text = (data.get("query") or "").strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="查询不能为空")

    async def generate():
        try:
            async for event in services.agent.run(
                user_input=query_text,
                user_id=user.id,
                model_id=data.get("model_id", ""),
                history=data.get("history", []),
                use_personal=data.get("use_personal", False),
                use_depth=data.get("use_depth", False),
                skill_prefs={},
                tool_overrides={},
            ):
                yield sse(event)
        except Exception as exc:
            logger.exception("[/api/query] failed")
            yield sse({"type": "error", "data": str(exc)})

    return StreamingResponse(generate(), media_type="text/event-stream", headers=SSE_HEADERS)


@router.post("/api/rag/search")
async def rag_search_debug(
    request: Request,
    user=Depends(get_current_user),
    services: WebServices = Depends(get_services),
):
    data = await request.json()
    query_text = (data.get("query") or "").strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="query 不能为空")
    rag_tool = services.registry.get("rag_search")
    if rag_tool is None:
        raise HTTPException(status_code=500, detail="rag_search 未注册")
    packet = await rag_tool.execute(
        query=query_text,
        mode=data.get("mode") or ("deep" if data.get("use_depth") else "normal"),
        include_personal=bool(data.get("include_personal") or data.get("use_personal")),
        focus=data.get("focus") or "general",
        top_k=int(data.get("top_k") or 10),
        user_id=user.id,
    )
    return JSONResponse(
        {
            "query": packet.query,
            "mode": packet.mode,
            "source_counts": packet.source_counts,
            "citations": packet.citations,
            "text": packet.to_tool_text(),
        }
    )
