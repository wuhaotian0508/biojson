from __future__ import annotations


def test_llm_gateway_sanitizes_deepseek_agent_params():
    from nutrimaster.config.llm import sanitize_params_for_model

    params = sanitize_params_for_model(
        "deepseek-v4",
        {
            "temperature": 0.7,
            "top_p": 0.9,
            "logprobs": True,
            "messages": [],
        },
        is_agent_call=True,
    )

    assert "temperature" not in params
    assert "top_p" not in params
    assert "logprobs" not in params
    assert params["extra_body"]["thinking"] == {"type": "enabled"}
    assert params["extra_body"]["reasoning_effort"] == "max"


def test_llm_gateway_does_not_fallback_after_selected_client_failure():
    import asyncio
    from types import SimpleNamespace

    import pytest

    from nutrimaster.config.llm import LLMGateway, LLMRoute

    class FakeCompletions:
        def __init__(self, response=None, exc=None):
            self.response = response
            self.exc = exc

        async def create(self, **kwargs):
            if self.exc:
                raise self.exc
            return self.response

    class FakeClient:
        def __init__(self, completions):
            self.chat = SimpleNamespace(completions=completions)

    message = SimpleNamespace(content="ok")
    gateway = LLMGateway(
        routes={
            "primary": LLMRoute(
                client=FakeClient(FakeCompletions(exc=RuntimeError("boom"))),
                model="primary-model",
            ),
            "fallback": LLMRoute(
                client=FakeClient(
                    FakeCompletions(
                        response=SimpleNamespace(choices=[SimpleNamespace(message=message)])
                    )
                ),
                model="fallback-model",
            ),
        },
    )

    with pytest.raises(RuntimeError, match="boom"):
        asyncio.run(gateway.call_llm([{"role": "user", "content": "hi"}]))
