def test_error_response_uses_standard_envelope_without_secret_details():
    from server.responses import error_response

    response = error_response(
        code="missing_api_key",
        message="Real service credentials are not configured",
        status_code=503,
        details={
            "missing": ["OPENAI_API_KEY"],
            "raw_exception": "Authorization: Bearer secret-token",
        },
    )

    assert response.status_code == 503
    assert response.body == {
        "error": {
            "code": "missing_api_key",
            "message": "Real service credentials are not configured",
            "details": {"missing": ["OPENAI_API_KEY"]},
        }
    }
