from __future__ import annotations

from pathlib import Path


def test_legacy_web_entrypoint_is_removed_after_package_cutover():
    root = Path(__file__).resolve().parents[2]
    source = (root / "src" / "server" / "web.py").read_text(encoding="utf-8")

    assert not (root / "rag" / "web" / "app.py").exists()
    assert "FastAPI(" in source
    assert "from server.auth" in source


def test_server_app_and_api_share_empty_retrieval_dependency():
    from server.api import _EmptyRetrievalService as ApiEmptyRetrievalService
    from server.app import _EmptyRetrievalService as AppEmptyRetrievalService
    from server.deps import EmptyRetrievalService

    assert ApiEmptyRetrievalService is EmptyRetrievalService
    assert AppEmptyRetrievalService is EmptyRetrievalService
