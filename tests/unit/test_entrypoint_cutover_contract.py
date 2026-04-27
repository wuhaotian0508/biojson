from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_root_vercel_entrypoint_is_removed():
    assert not (ROOT / "api").exists()


def test_headless_api_entrypoint_is_packaged_without_sys_path_hack():
    source = (ROOT / "src" / "server" / "headless.py").read_text(
        encoding="utf-8"
    )

    assert "sys.path.insert" not in source
    assert "from server.api" in source
