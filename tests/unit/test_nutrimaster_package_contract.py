import tomllib
import os
import subprocess
import sys
from pathlib import Path


def test_project_name_is_nutrimaster_and_top_level_packages_are_importable():
    package = __import__("nutrimaster")
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert package.__name__ == "nutrimaster"
    assert pyproject["project"]["name"] == "nutrimaster"


def test_extraction_package_is_importable_outside_source_working_directory(tmp_path):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)

    result = subprocess.run(
        [sys.executable, "-c", "import nutrimaster.extraction; print(nutrimaster.extraction.__file__)"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_settings_report_required_real_service_keys():
    from nutrimaster.config.settings import Settings

    settings = Settings.from_env({})

    assert settings.missing_real_service_keys() == [
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "MAIN_MODEL",
        "JINA_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
    ]
