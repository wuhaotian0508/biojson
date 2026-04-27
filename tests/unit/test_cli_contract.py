import json


def test_serve_check_config_reports_missing_real_service_keys(capsys):
    from cli.main import main

    exit_code = main(["serve", "--check-config"], env={})
    captured = capsys.readouterr()

    assert exit_code == 2
    assert json.loads(captured.out) == {
        "error": {
            "code": "missing_real_service_config",
            "message": "NutriMaster real-service configuration is incomplete",
            "details": {
                "missing": [
                    "OPENAI_API_KEY",
                    "OPENAI_BASE_URL",
                    "MODEL",
                    "JINA_API_KEY",
                    "SUPABASE_URL",
                    "SUPABASE_SERVICE_ROLE_KEY",
                ]
            },
        }
    }


def test_serve_check_config_succeeds_when_real_service_keys_exist(capsys):
    from cli.main import main

    env = {
        "OPENAI_API_KEY": "test-key",
        "OPENAI_BASE_URL": "https://example.test/v1",
        "MODEL": "test-model",
        "JINA_API_KEY": "test-jina",
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-service-role",
    }

    exit_code = main(["serve", "--check-config"], env=env)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert json.loads(captured.out) == {
        "status": "ok",
        "service": "biojson",
        "mode": "serve",
    }
