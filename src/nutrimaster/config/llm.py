from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI, OpenAI, Timeout

from nutrimaster.config.settings import Settings

logger = logging.getLogger(__name__)

_DEEPSEEK_REASONER_MODELS = {"deepseek-reasoner", "deepseek-r1", "deepseek-v4"}
_DEEPSEEK_IGNORED_PARAMS = {"temperature", "top_p", "presence_penalty", "frequency_penalty"}
_DEEPSEEK_FORBIDDEN_PARAMS = {"logprobs", "top_logprobs"}
_DEEPSEEK_DEFAULT_THINKING = {"type": "enabled"}
_DEEPSEEK_DEFAULT_EFFORT = "high"
_TIMEOUT = Timeout(timeout=300.0, connect=10.0)


def is_deepseek_reasoner(model_name: str) -> bool:
    name = model_name.lower()
    return any(model in name for model in _DEEPSEEK_REASONER_MODELS)


def sanitize_params_for_model(
    model_name: str,
    params: dict[str, Any],
    *,
    is_agent_call: bool = False,
) -> dict[str, Any]:
    params = dict(params)
    if not is_deepseek_reasoner(model_name):
        return params
    for key in _DEEPSEEK_IGNORED_PARAMS | _DEEPSEEK_FORBIDDEN_PARAMS:
        params.pop(key, None)
    extra_body = dict(params.get("extra_body", {}))
    extra_body.setdefault("thinking", _DEEPSEEK_DEFAULT_THINKING.copy())
    extra_body.setdefault("reasoning_effort", "max" if is_agent_call else _DEEPSEEK_DEFAULT_EFFORT)
    params["extra_body"] = extra_body
    return params


@dataclass(frozen=True)
class LLMRoute:
    client: Any
    model: str


class LLMGateway:
    def __init__(self, *, routes: dict[str, LLMRoute], fallback_route_id: str | None = None):
        self.routes = routes
        self.fallback_route_id = fallback_route_id

    def _resolve(self, model_id: str = "") -> tuple[str, LLMRoute]:
        route_id = model_id or "primary"
        return route_id, self.routes.get(route_id) or self.routes["primary"]

    def _candidate_routes(self, model_id: str = "") -> list[tuple[str, LLMRoute]]:
        route_id, route = self._resolve(model_id)
        candidates = [(route_id, route)]
        if self.fallback_route_id and self.fallback_route_id in self.routes and route_id != self.fallback_route_id:
            candidates.append((self.fallback_route_id, self.routes[self.fallback_route_id]))
        return candidates

    async def call_llm(
        self,
        messages,
        tools=None,
        model_id: str = "",
        is_agent_call: bool = False,
        **kwargs,
    ):
        last_error = None
        for route_id, route in self._candidate_routes(model_id):
            try:
                params = {"model": route.model, "messages": messages, **kwargs}
                if tools:
                    params["tools"] = tools
                params = sanitize_params_for_model(
                    route.model,
                    params,
                    is_agent_call=is_agent_call,
                )
                response = await route.client.chat.completions.create(**params)
                return response.choices[0].message
            except Exception as exc:
                logger.warning("[%s] LLM call failed: %s", route_id, exc)
                last_error = exc
        raise last_error

    async def call_llm_stream(
        self,
        messages,
        model_id: str = "",
        is_agent_call: bool = False,
        **kwargs,
    ):
        last_error = None
        for route_id, route in self._candidate_routes(model_id):
            try:
                params = {"model": route.model, "messages": messages, "stream": True, **kwargs}
                params = sanitize_params_for_model(
                    route.model,
                    params,
                    is_agent_call=is_agent_call,
                )
                response = await route.client.chat.completions.create(**params)
                async for chunk in response:
                    yield chunk
                return
            except Exception as exc:
                logger.warning("[%s] LLM stream failed: %s", route_id, exc)
                last_error = exc
        if last_error:
            raise last_error


def create_llm_gateway(settings: Settings | None = None) -> LLMGateway:
    settings = settings or Settings.from_env()
    routes = {
        "primary": LLMRoute(
            client=AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                timeout=_TIMEOUT,
            ),
            model=settings.model,
        )
    }
    fallback_route_id = None
    if settings.fallback_api_key:
        routes["fallback"] = LLMRoute(
            client=AsyncOpenAI(
                api_key=settings.fallback_api_key,
                base_url=settings.fallback_base_url,
                timeout=_TIMEOUT,
            ),
            model=settings.fallback_model or settings.model,
        )
        fallback_route_id = "fallback"
    return LLMGateway(routes=routes, fallback_route_id=fallback_route_id)


def create_sync_client(settings: Settings | None = None):
    settings = settings or Settings.from_env()
    return OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        timeout=_TIMEOUT,
    )


_DEFAULT_GATEWAY: LLMGateway | None = None
_DEFAULT_SYNC_CLIENT = None


def default_gateway() -> LLMGateway:
    global _DEFAULT_GATEWAY
    if _DEFAULT_GATEWAY is None:
        _DEFAULT_GATEWAY = create_llm_gateway()
    return _DEFAULT_GATEWAY


async def call_llm(*args, **kwargs):
    return await default_gateway().call_llm(*args, **kwargs)


async def call_llm_stream(*args, **kwargs):
    async for chunk in default_gateway().call_llm_stream(*args, **kwargs):
        yield chunk


def call_llm_sync(messages, is_agent_call: bool = False, **kwargs):
    global _DEFAULT_SYNC_CLIENT
    settings = Settings.from_env()
    if _DEFAULT_SYNC_CLIENT is None:
        _DEFAULT_SYNC_CLIENT = create_sync_client(settings)
    params = {"model": settings.model, "messages": messages, **kwargs}
    params = sanitize_params_for_model(settings.model, params, is_agent_call=is_agent_call)
    response = _DEFAULT_SYNC_CLIENT.chat.completions.create(**params)
    return response.choices[0].message
