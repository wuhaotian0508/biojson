from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient


class FakeAgentRuntime:
    def __init__(self):
        self.calls = []

    async def run(self, **kwargs):
        self.calls.append(kwargs)
        yield {"type": "text", "data": "hello"}
        yield {"type": "done"}


def test_app_factory_health_uses_injected_retrieval_service():
    from server.app import create_app

    app = create_app(retrieval_service=SimpleNamespace(total_chunks=42))
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "total_chunks": 42}


def test_app_factory_config_returns_public_supabase_settings():
    from server.app import create_app
    from shared.settings import Settings

    settings = Settings.from_env(
        {
            "SUPABASE_URL": "https://example.supabase.co",
            "NEXT_PUBLIC_SUPABASE_ANON_KEY": "anon-key",
            "SITE_URL": "https://nutrimaster.example",
            "ADMIN_PORT": "5600",
        }
    )
    app = create_app(settings=settings, retrieval_service=SimpleNamespace(total_chunks=0))
    client = TestClient(app)

    response = client.get("/api/config")

    assert response.status_code == 200
    assert response.json() == {
        "supabase_url": "https://example.supabase.co",
        "supabase_anon_key": "anon-key",
        "admin_port": 5600,
        "site_url": "https://nutrimaster.example",
        "models": [],
    }


def test_query_route_streams_agent_events_from_injected_runtime():
    from server.app import create_app

    agent_runtime = FakeAgentRuntime()
    app = create_app(
        retrieval_service=SimpleNamespace(total_chunks=0),
        agent_runtime=agent_runtime,
    )
    client = TestClient(app)

    response = client.post(
        "/api/query",
        json={
            "query": "What is lycopene?",
            "model_id": "primary",
            "history": [{"role": "user", "content": "previous"}],
            "use_personal": True,
            "use_depth": True,
            "skill_prefs": {"rag-answer": "must_use"},
            "tool_overrides": {"execute_shell": "enabled"},
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert 'data: {"type": "text", "data": "hello"}' in response.text
    assert 'data: {"type": "done"}' in response.text
    assert agent_runtime.calls == [
        {
            "user_input": "What is lycopene?",
            "user_id": None,
            "model_id": "primary",
            "history": [{"role": "user", "content": "previous"}],
            "use_personal": True,
            "use_depth": True,
            "skill_prefs": {"rag-answer": "must_use"},
            "tool_overrides": {"execute_shell": "enabled"},
        }
    ]


def test_query_route_rejects_empty_query():
    from server.app import create_app

    app = create_app(retrieval_service=SimpleNamespace(total_chunks=0))
    client = TestClient(app)

    response = client.post("/api/query", json={"query": "  "})

    assert response.status_code == 400
    assert response.json() == {"detail": "查询不能为空"}
