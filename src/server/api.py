from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from server.deps import EmptyRetrievalService


class QueryRequest(BaseModel):
    query: str = Field(..., description="用户查询文本")
    model_id: str = Field("primary", description="模型 ID")
    use_depth: bool = Field(False, description="是否启用深度模式")


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict] = Field(default_factory=list)
    tool_calls: list[dict] = Field(default_factory=list)
    steps: int


_EmptyRetrievalService = EmptyRetrievalService


def create_api_app(
    *,
    agent_runtime: Any,
    retrieval_service: Any | None = None,
    tool_names: Iterable[str] | None = None,
    skill_count: Callable[[], int] | None = None,
    tools: Iterable[Any] | None = None,
) -> FastAPI:
    """Create the headless RAG API app with injected runtime dependencies."""

    retrieval_service = retrieval_service or _EmptyRetrievalService()
    tool_names = set(tool_names or set())
    skill_count = skill_count or (lambda: 0)
    tools = list(tools or [])

    app = FastAPI(title="RAG API", version="1.0.0")

    @app.get("/api/health")
    async def health():
        return JSONResponse(
            {
                "status": "ok",
                "total_chunks": retrieval_service.total_chunks,
                "tools": sorted(tool_names),
                "skills": skill_count(),
            }
        )

    @app.get("/api/tools")
    async def list_tools():
        return JSONResponse(
            {
                "tools": [
                    {"name": tool.name, "description": tool.description}
                    for tool in tools
                ]
            }
        )

    @app.post("/api/query", response_model=QueryResponse)
    async def query(req: QueryRequest):
        try:
            answer_parts = []
            sources = []
            tool_calls = []
            steps = 0
            async for event in agent_runtime.run(
                user_input=req.query,
                user_id=None,
                model_id=req.model_id,
                history=[],
                use_depth=req.use_depth,
                use_personal=False,
                skill_prefs={},
                tool_overrides={},
            ):
                event_type = event.get("type")
                if event_type == "text":
                    answer_parts.append(event.get("data", ""))
                elif event_type == "tool_call":
                    steps += 1
                    tool_calls.append(
                        {
                            "tool": event.get("tool"),
                            "args": event.get("args"),
                        }
                    )
                elif event_type == "sources":
                    sources = event.get("data", [])
                elif event_type == "error":
                    raise HTTPException(status_code=500, detail=event.get("data"))

            return QueryResponse(
                answer="".join(answer_parts),
                sources=sources,
                tool_calls=tool_calls,
                steps=steps,
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/query/stream")
    async def query_stream(req: QueryRequest):
        async def event_generator():
            try:
                async for event in agent_runtime.run(
                    user_input=req.query,
                    user_id=None,
                    model_id=req.model_id,
                    history=[],
                    use_depth=req.use_depth,
                    use_personal=False,
                    skill_prefs={},
                    tool_overrides={},
                ):
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            except Exception as exc:
                yield f"data: {json.dumps({'type': 'error', 'data': str(exc)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    return app
