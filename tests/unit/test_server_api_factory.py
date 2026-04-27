from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient


class FakeAgentRuntime:
    async def run(self, **kwargs):
        yield {"type": "tool_call", "tool": "rag_search", "args": {"query": kwargs["user_input"]}}
        yield {"type": "sources", "data": [{"title": "source-a"}]}
        yield {"type": "text", "data": "answer "}
        yield {"type": "text", "data": "text"}
        yield {"type": "done"}


def test_api_factory_sync_query_collects_agent_events():
    from server.api import create_api_app

    app = create_api_app(
        agent_runtime=FakeAgentRuntime(),
        retrieval_service=SimpleNamespace(total_chunks=3),
        tool_names={"rag_search", "execute_shell"},
        skill_count=lambda: 2,
    )
    client = TestClient(app)

    response = client.post("/api/query", json={"query": "lycopene", "model_id": "primary"})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "answer text",
        "sources": [{"title": "source-a"}],
        "tool_calls": [{"tool": "rag_search", "args": {"query": "lycopene"}}],
        "steps": 1,
    }


def test_api_factory_stream_query_forwards_sse_events():
    from server.api import create_api_app

    app = create_api_app(
        agent_runtime=FakeAgentRuntime(),
        retrieval_service=SimpleNamespace(total_chunks=3),
        tool_names={"rag_search"},
        skill_count=lambda: 1,
    )
    client = TestClient(app)

    response = client.post("/api/query/stream", json={"query": "lycopene"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert 'data: {"type": "text", "data": "answer "}' in response.text
    assert 'data: {"type": "done"}' in response.text


def test_api_factory_health_and_tools_use_injected_stack_metadata():
    from server.api import create_api_app

    app = create_api_app(
        agent_runtime=FakeAgentRuntime(),
        retrieval_service=SimpleNamespace(total_chunks=3),
        tool_names={"rag_search", "execute_shell"},
        skill_count=lambda: 2,
        tools=[SimpleNamespace(name="rag_search", description="Search")],
    )
    client = TestClient(app)

    assert client.get("/api/health").json() == {
        "status": "ok",
        "total_chunks": 3,
        "tools": ["execute_shell", "rag_search"],
        "skills": 2,
    }
    assert client.get("/api/tools").json() == {
        "tools": [{"name": "rag_search", "description": "Search"}]
    }
