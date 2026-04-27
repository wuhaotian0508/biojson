from __future__ import annotations

import inspect


def test_email_sender_uses_nutrimaster_settings_not_legacy_core_config():
    import server.email_sender as email_sender

    source = inspect.getsource(email_sender)

    assert "rag.web" not in source
    assert "core.config" not in source
    assert "sys.path.insert" not in source
    assert "Settings.from_env" in source
