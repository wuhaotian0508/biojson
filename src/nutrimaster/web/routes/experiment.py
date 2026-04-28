from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from nutrimaster.auth.service import get_current_user
from nutrimaster.web.deps import SSE_HEADERS, WebServices, get_services, sse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/experiment/preview")
async def experiment_preview(
    request: Request,
    user=Depends(get_current_user),
    services: WebServices = Depends(get_services),
):
    data = await request.json()
    goal = (data.get("goal") or data.get("query") or data.get("answer_text") or "").strip()
    genes = data.get("genes") or None
    selected_gene_names = data.get("selected_gene_names") or data.get("user_genes") or None
    if not goal and not genes:
        raise HTTPException(status_code=400, detail="缺少 goal 或 genes")
    try:
        preview = await services.experiment_service.preview(
            goal=goal,
            genes=genes,
            selected_gene_names=selected_gene_names,
        )
    except Exception as exc:
        logger.exception("[/api/experiment/preview] failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return JSONResponse({"genes": preview})


@router.post("/api/experiment/run")
async def experiment_run(
    request: Request,
    user=Depends(get_current_user),
    services: WebServices = Depends(get_services),
):
    data = await request.json()
    genes = data.get("genes")
    if not genes:
        raise HTTPException(status_code=400, detail="缺少 genes 列表")

    async def generate():
        try:
            yield sse({"type": "progress", "step": 1, "total": 1, "msg": "正在执行一键实验 pipeline..."})
            sops = await services.experiment_service.run(genes=genes)
            yield sse({"type": "result", "sops": sops})
            yield sse({"type": "done"})
        except Exception as exc:
            logger.exception("[/api/experiment/run] failed")
            yield sse({"type": "error", "data": str(exc)})

    return StreamingResponse(generate(), media_type="text/event-stream", headers=SSE_HEADERS)
