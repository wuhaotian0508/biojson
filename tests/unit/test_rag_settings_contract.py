from __future__ import annotations

from pathlib import Path


def test_rag_settings_default_paths_are_project_relative(tmp_path: Path):
    from shared.settings import Settings

    settings = Settings.from_env({"NUTRIMASTER_ROOT": str(tmp_path)})

    assert settings.project_root == tmp_path
    assert settings.rag.data_dir == tmp_path / "data" / "corpus"
    assert settings.rag.index_dir == tmp_path / "data" / "index"
    assert settings.rag.personal_lib_dir == tmp_path / "data" / "personal_lib"


def test_rag_settings_honor_env_overrides(tmp_path: Path):
    from shared.settings import Settings

    env = {
        "NUTRIMASTER_ROOT": str(tmp_path),
        "RAG_DATA_DIR": str(tmp_path / "custom-data"),
        "RAG_INDEX_DIR": str(tmp_path / "custom-index"),
        "RAG_PERSONAL_LIB_DIR": str(tmp_path / "custom-personal"),
        "TOP_K_RETRIEVAL": "7",
        "TOP_K_RERANK": "3",
        "WEB_HOST": "127.0.0.1",
        "WEB_PORT": "5100",
        "ADMIN_PORT": "5600",
        "DEBUG": "true",
    }

    settings = Settings.from_env(env)

    assert settings.rag.data_dir == tmp_path / "custom-data"
    assert settings.rag.index_dir == tmp_path / "custom-index"
    assert settings.rag.personal_lib_dir == tmp_path / "custom-personal"
    assert settings.rag.top_k_retrieval == 7
    assert settings.rag.top_k_rerank == 3
    assert settings.rag.web_host == "127.0.0.1"
    assert settings.rag.web_port == 5100
    assert settings.rag.admin_port == 5600
    assert settings.rag.debug is True
