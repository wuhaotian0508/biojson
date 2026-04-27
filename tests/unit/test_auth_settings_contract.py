from __future__ import annotations

import inspect


def test_fastapi_auth_uses_nutrimaster_settings_not_legacy_core_config():
    import server.auth as auth

    source = inspect.getsource(auth)

    assert "rag.web" not in source
    assert "core.config" not in source
    assert "Settings.from_env" in source
