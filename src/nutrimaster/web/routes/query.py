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
    history = data.get("history", []) or []
    use_personal = data.get("use_personal", False)
    use_depth = data.get("use_depth", False)
    model_id = data.get("model_id", "")
    system_prompt = services.agent.prompt_builder.build(
        user_id=user.id,
        use_depth=use_depth,
        use_personal=use_personal,
    )
    initial_messages = [
        {"role": "system", "content": system_prompt},
        *services.agent._truncate_history(history),
        {"role": "user", "content": query_text},
    ]
    initial_messages = services.agent._strip_reasoning_for_new_turn(initial_messages)
    capture_session = services.interaction_recorder.start(
        user_id=user.id,
        session_id=data.get("session_id") or "",
        client_turn_id=data.get("client_turn_id") or "",
        query=query_text,
        model_id=model_id,
        history=history,
        initial_messages=initial_messages,
        use_personal=use_personal,
        use_depth=use_depth,
        capture_consent=bool(data.get("capture_consent")),
    )

    async def generate():
        status = "completed"
        try:
            yield sse(
                {
                    "type": "capture",
                    "enabled": capture_session.active,
                    "interaction_id": capture_session.interaction_id if capture_session.active else "",
                    "turn_id": capture_session.turn_id,
                }
            )
            async for event in services.agent.run(
                user_input=query_text,
                user_id=user.id,
                model_id=model_id,
                history=history,
                use_personal=use_personal,
                use_depth=use_depth,
                skill_prefs={},
                tool_overrides={},
            ):
                capture_session.capture_event(event)
                if event.get("type") == "error":
                    status = "error"
                yield sse(event)
        except Exception as exc:
            logger.exception("[/api/query] failed")
            status = "error"
            capture_session.capture_event({"type": "error", "data": str(exc)})
            yield sse({"type": "error", "data": str(exc)})
        finally:
            capture_session.finish(status=status)

    return StreamingResponse(generate(), media_type="text/event-stream", headers=SSE_HEADERS)


@router.post("/api/feedback")
async def feedback(
    request: Request,
    user=Depends(get_current_user),
    services: WebServices = Depends(get_services),
):
    data = await request.json()
    interaction_id = (data.get("interaction_id") or "").strip()
    rating = (data.get("rating") or "").strip().lower()
    if not interaction_id:
        raise HTTPException(status_code=400, detail="interaction_id 不能为空")
    if rating not in {"up", "down"}:
        raise HTTPException(status_code=400, detail="rating 必须是 up 或 down")
    payload = services.interaction_recorder.record_feedback(
        user_id=user.id,
        interaction_id=interaction_id,
        session_id=data.get("session_id") or "",
        turn_id=data.get("turn_id") or data.get("client_turn_id") or "",
        rating=rating,
        comment=(data.get("comment") or "").strip(),
        tags=data.get("tags") or [],
    )
    return JSONResponse({"status": "ok", "feedback_id": payload["feedback_id"]})


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
        pubmed_query=data.get("pubmed_query") or "",
        gene_db_query=data.get("gene_db_query") or "",
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
