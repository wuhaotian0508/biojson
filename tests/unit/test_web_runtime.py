from pathlib import Path

from shared.settings import Settings


ROOT = Path(__file__).resolve().parents[2]


def test_web_config_defaults_debug_off(monkeypatch):
    monkeypatch.delenv("DEBUG", raising=False)

    settings = Settings.from_env(env={}, project_root=ROOT)

    assert settings.rag is not None
    assert settings.rag.debug is False
