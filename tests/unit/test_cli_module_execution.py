from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_cli_package_is_executable_with_python_m():
    env = {
        **os.environ,
        "PYTHONPATH": str(ROOT / "src"),
        "OPENAI_API_KEY": "test-key",
        "OPENAI_BASE_URL": "https://example.test/v1",
        "MODEL": "test-model",
        "JINA_API_KEY": "test-jina",
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-service-role",
    }

    result = subprocess.run(
        [sys.executable, "-m", "nutrimaster", "serve", "--check-config"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "status": "ok",
        "service": "nutrimaster",
        "mode": "serve",
    }


def test_cli_check_config_loads_dotenv_from_working_directory(tmp_path: Path):
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "OPENAI_API_KEY=test-key",
                "OPENAI_BASE_URL=https://example.test/v1",
                "MODEL=test-model",
                "JINA_API_KEY=test-jina",
                "SUPABASE_URL=https://example.supabase.co",
                "SUPABASE_SERVICE_ROLE_KEY=test-service-role",
            ]
        ),
        encoding="utf-8",
    )
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(ROOT / "src"),
    }

    result = subprocess.run(
        [sys.executable, "-m", "nutrimaster", "serve", "--check-config"],
        cwd=tmp_path,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "status": "ok",
        "service": "nutrimaster",
        "mode": "serve",
    }


def test_cli_check_config_command_is_executable_with_python_m():
    env = {
        **os.environ,
        "PYTHONPATH": str(ROOT / "src"),
        "OPENAI_API_KEY": "test-key",
        "OPENAI_BASE_URL": "https://example.test/v1",
        "MODEL": "test-model",
        "JINA_API_KEY": "test-jina",
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-service-role",
    }

    result = subprocess.run(
        [sys.executable, "-m", "nutrimaster", "check-config"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "status": "ok",
        "service": "nutrimaster",
        "mode": "check-config",
    }
