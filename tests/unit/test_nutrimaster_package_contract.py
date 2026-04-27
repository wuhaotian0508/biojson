import tomllib
from pathlib import Path


def test_project_name_is_biojson_and_top_level_packages_are_importable():
    package = __import__("cli")
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert package.__name__ == "cli"
    assert pyproject["project"]["name"] == "biojson"


def test_settings_report_required_real_service_keys():
    from shared.settings import Settings

    settings = Settings.from_env({})

    assert settings.missing_real_service_keys() == [
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "MODEL",
        "JINA_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
    ]
