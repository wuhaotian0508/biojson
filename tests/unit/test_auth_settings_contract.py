from __future__ import annotations

import asyncio
import inspect
from starlette.requests import Request
import pytest


def test_fastapi_auth_uses_nutrimaster_settings_not_legacy_core_config():
    import nutrimaster.auth.service as auth

    source = inspect.getsource(auth)

    assert "rag.web" not in source
    assert "core.config" not in source
    assert "Settings.from_env" in source


def _request(headers: dict[str, str] | None = None) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/query",
            "headers": [
                (key.lower().encode("latin-1"), value.encode("latin-1"))
                for key, value in (headers or {}).items()
            ],
        }
    )


def test_dev_auth_bypass_returns_fixed_user_without_token(monkeypatch):
    import nutrimaster.auth.service as auth

    monkeypatch.setenv("NUTRIMASTER_DEV_AUTH_BYPASS", "1")
    monkeypatch.setenv("NUTRIMASTER_DEV_AUTH_USER_ID", "dev-user")
    monkeypatch.setenv("NUTRIMASTER_DEV_AUTH_EMAIL", "dev@example.com")

    user = asyncio.run(auth.get_current_user(_request()))

    assert user.id == "dev-user"
    assert user.email == "dev@example.com"
    assert user.user_metadata["nickname"] == "dev"


def test_auth_requires_token_when_dev_bypass_is_off(monkeypatch):
    import nutrimaster.auth.service as auth

    monkeypatch.delenv("NUTRIMASTER_DEV_AUTH_BYPASS", raising=False)

    with pytest.raises(Exception) as exc_info:
        asyncio.run(auth.get_current_user(_request()))

    assert getattr(exc_info.value, "status_code", None) == 401
