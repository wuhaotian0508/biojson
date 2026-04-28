from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_runtime_code_lives_under_single_nutrimaster_package():
    package_root = ROOT / "src" / "nutrimaster"

    assert package_root.is_dir()
    for subpackage in (
        "agent",
        "auth",
        "config",
        "crispr",
        "extraction",
        "rag",
        "web",
    ):
        assert (package_root / subpackage).is_dir(), subpackage
    assert (package_root / "agent" / "tools").is_dir()
    assert (package_root / "agent" / "skills" / "shared").is_dir()
    assert not (package_root / "tools").exists()
    assert not (package_root / "skills").exists()


def test_old_top_level_runtime_packages_are_removed():
    obsolete = [
        "admin",
        "agent",
        "app",
        "crispr",
        "domain",
        "indexing",
        "retrieval",
        "server",
        "shared",
        "storage",
        "tools",
    ]

    assert [name for name in obsolete if (ROOT / "src" / name).exists()] == []
    assert not (ROOT / "extractor").exists()


def test_headless_api_and_standalone_admin_commands_are_removed():
    cli_source = (ROOT / "src" / "nutrimaster" / "cli.py").read_text(encoding="utf-8")

    assert 'subparsers.add_parser("api")' not in cli_source
    assert 'subparsers.add_parser("admin")' not in cli_source
    assert "server.headless" not in cli_source
    assert "admin.app" not in cli_source
