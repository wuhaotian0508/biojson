"""
LLM 客户端网关 — 所有 LLM 调用的统一入口

功能：
  - 主/备自动切换（primary → fallback）
  - model_id 路由（从 config.MODEL_OPTIONS 动态选择客户端）
  - 异步调用 call_llm()（支持 tool calling）
  - 异步流式 call_llm_stream()（逐 chunk yield）
  - 同步调用 call_llm_sync()（供 CRISPR pipeline 等同步代码使用）

所有配置从 config.py 读取，不再从环境变量独立读取。
"""
from __future__ import annotations

import logging
from openai import AsyncOpenAI, OpenAI

from core.config import (
    LLM_API_KEY, LLM_BASE_URL, LLM_MODEL,
    FALLBACK_API_KEY, FALLBACK_BASE_URL, FALLBACK_MODEL,
    MODEL_OPTIONS,
)

logger = logging.getLogger(__name__)

# ---- 模块级客户端（启动时创建一次） ----
primary_client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
fallback_client = (
    AsyncOpenAI(api_key=FALLBACK_API_KEY, base_url=FALLBACK_BASE_URL)
    if FALLBACK_API_KEY else None
)
PRIMARY_MODEL = LLM_MODEL
FALLBACK_MODEL_NAME = FALLBACK_MODEL or LLM_MODEL

# 同步客户端（供 CRISPR pipeline 等同步调用）
primary_sync = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
fallback_sync = (
    OpenAI(api_key=FALLBACK_API_KEY, base_url=FALLBACK_BASE_URL)
    if FALLBACK_API_KEY else None
)

# 异步客户端缓存：model_id → (AsyncOpenAI, model_name)
_async_cache: dict[str, tuple[AsyncOpenAI, str]] = {}


def _resolve_async_client(model_id: str = "") -> tuple[AsyncOpenAI, str]:
    """根据 model_id 获取异步客户端+模型名（带缓存）。"""
    if not model_id or model_id == "primary":
        return primary_client, PRIMARY_MODEL
    if model_id == "fallback" and fallback_client:
        return fallback_client, FALLBACK_MODEL_NAME
    if model_id in _async_cache:
        return _async_cache[model_id]
    for opt in MODEL_OPTIONS:
        if opt["id"] == model_id:
            c = AsyncOpenAI(api_key=opt["api_key"], base_url=opt.get("base_url"))
            pair = (c, opt["model"])
            _async_cache[model_id] = pair
            return pair
    return primary_client, PRIMARY_MODEL


# ------------------------------------------------------------------
# 异步调用（支持 tool calling）
# ------------------------------------------------------------------
async def call_llm(messages, tools=None, model_id: str = "", **kwargs):
    """主+备异步调用。返回 response.choices[0].message。

    支持 model_id 路由：从 MODEL_OPTIONS 动态选择客户端。
    """
    client, model = _resolve_async_client(model_id)
    configs = [(client, model, "selected")]
    if fallback_client and client is not fallback_client:
        configs.append((fallback_client, FALLBACK_MODEL_NAME, "fallback"))

    last_err = None
    for c, m, label in configs:
        try:
            params = dict(model=m, messages=messages, **kwargs)
            if tools:
                params["tools"] = tools
            response = await c.chat.completions.create(**params)
            return response.choices[0].message
        except Exception as e:
            logger.warning("[%s] LLM 调用失败: %s", label, e)
            last_err = e
    raise last_err


# ------------------------------------------------------------------
# 异步流式调用（yield raw chunks）
# ------------------------------------------------------------------
async def call_llm_stream(messages, model_id: str = "", **kwargs):
    """主+备异步流式调用。Yield 原始 chunk 对象。"""
    client, model = _resolve_async_client(model_id)
    configs = [(client, model, "selected")]
    if fallback_client and client is not fallback_client:
        configs.append((fallback_client, FALLBACK_MODEL_NAME, "fallback"))

    last_err = None
    for c, m, label in configs:
        try:
            response = await c.chat.completions.create(
                model=m, messages=messages, stream=True, **kwargs,
            )
            async for chunk in response:
                yield chunk
            return
        except Exception as e:
            logger.warning("[%s] LLM 流式调用失败: %s", label, e)
            last_err = e
    if last_err:
        raise last_err


# ------------------------------------------------------------------
# 同步调用（供 CRISPR pipeline 等同步代码使用）
# ------------------------------------------------------------------
def call_llm_sync(messages, **kwargs):
    """主+备同步调用。返回 response.choices[0].message。"""
    configs = [(primary_sync, PRIMARY_MODEL, "primary")]
    if fallback_sync:
        configs.append((fallback_sync, FALLBACK_MODEL_NAME, "fallback"))

    last_err = None
    for c, m, label in configs:
        try:
            response = c.chat.completions.create(
                model=m, messages=messages, **kwargs,
            )
            return response.choices[0].message
        except Exception as e:
            logger.warning("[%s] 同步 LLM 调用失败: %s", label, e)
            last_err = e
    raise last_err
