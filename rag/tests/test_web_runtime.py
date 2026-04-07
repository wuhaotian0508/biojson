import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RAG_DIR = ROOT / "rag"
WEB_DIR = RAG_DIR / "web"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(RAG_DIR))
sys.path.insert(0, str(WEB_DIR))


def test_web_config_defaults_debug_off(monkeypatch):
    monkeypatch.delenv("DEBUG", raising=False)

    config = importlib.import_module("rag.config")
    config = importlib.reload(config)

    assert config.DEBUG is False
