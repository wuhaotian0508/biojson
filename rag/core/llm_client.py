"""
LLM 客户端网关 — 所有 LLM 调用的统一入口

功能：
  - 主/备自动切换（primary → fallback）
  - model_id 路由（从 config.MODEL_OPTIONS 动态选择客户端）
  - 异步调用 call_llm()（支持 tool calling）
  - 异步流式 call_llm_stream()（逐 chunk yield）
  - 同步调用 call_llm_sync()（供 CRISPR pipeline 等同步代码使用）

模型差异处理：
  - GPT-5.4: 标准 OpenAI tool calling，支持 temperature 等参数
  - DeepSeek reasoner (V3.2): 支持 tool calling，但需要：
    1. 同一轮工具调用循环内回传 reasoning_content
    2. thinking 模式下 temperature/top_p 等参数被忽略，不传以避免警告
    3. assistant message 需保留 reasoning_content 字段

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

# DeepSeek reasoner 系列模型（V3.2 已支持 tool calling，但参数处理不同）
_DEEPSEEK_REASONER_MODELS = {"deepseek-reasoner", "deepseek-r1"}

# DeepSeek reasoner thinking 模式下会忽略这些参数，主动移除以避免 API 警告
_DEEPSEEK_IGNORED_PARAMS = {"temperature", "top_p", "presence_penalty", "frequency_penalty"}

# DeepSeek reasoner thinking 模式下传这些参数会报 400 错误
_DEEPSEEK_FORBIDDEN_PARAMS = {"logprobs", "top_logprobs"}


def is_deepseek_reasoner(model_name: str) -> bool:
    """判断是否为 DeepSeek reasoner 系列模型。"""
    name = model_name.lower()
    return any(m in name for m in _DEEPSEEK_REASONER_MODELS)


def _sanitize_params_for_model(model_name: str, params: dict) -> dict:
    """根据模型类型清理不兼容的参数。"""
    if not is_deepseek_reasoner(model_name):
        return params
    # DeepSeek reasoner: 移除 thinking 模式下会忽略或报错的参数
    for key in _DEEPSEEK_IGNORED_PARAMS | _DEEPSEEK_FORBIDDEN_PARAMS:
        params.pop(key, None)
    return params


# ---- 模块级客户端（启动时创建一次） ----
# 增加超时时间到 5 分钟，避免多轮工具调用时超时
from openai import Timeout
_TIMEOUT = Timeout(timeout=300.0, connect=10.0)

primary_client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL, timeout=_TIMEOUT)
fallback_client = (
    AsyncOpenAI(api_key=FALLBACK_API_KEY, base_url=FALLBACK_BASE_URL, timeout=_TIMEOUT)
    if FALLBACK_API_KEY else None
)
PRIMARY_MODEL = LLM_MODEL
FALLBACK_MODEL_NAME = FALLBACK_MODEL or LLM_MODEL

# 同步客户端（供 CRISPR pipeline 等同步调用）
primary_sync = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL, timeout=_TIMEOUT)
fallback_sync = (
    OpenAI(api_key=FALLBACK_API_KEY, base_url=FALLBACK_BASE_URL, timeout=_TIMEOUT)
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
            c = AsyncOpenAI(api_key=opt["api_key"], base_url=opt.get("base_url"), timeout=_TIMEOUT)
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
    DeepSeek reasoner: 支持 tools，但自动移除 temperature 等不兼容参数。
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
            # 根据模型清理不兼容参数
            params = _sanitize_params_for_model(m, params)
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
    """主+备异步流式调用。Yield 原始 chunk 对象。
    DeepSeek reasoner: 自动移除不兼容参数。
    """
    client, model = _resolve_async_client(model_id)
    configs = [(client, model, "selected")]
    if fallback_client and client is not fallback_client:
        configs.append((fallback_client, FALLBACK_MODEL_NAME, "fallback"))

    last_err = None
    for c, m, label in configs:
        try:
            params = dict(model=m, messages=messages, stream=True, **kwargs)
            params = _sanitize_params_for_model(m, params)
            response = await c.chat.completions.create(**params)
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
    """主+备同步调用。返回 response.choices[0].message。
    DeepSeek reasoner: 自动移除不兼容参数。
    """
    configs = [(primary_sync, PRIMARY_MODEL, "primary")]
    if fallback_sync:
        configs.append((fallback_sync, FALLBACK_MODEL_NAME, "fallback"))

    last_err = None
    for c, m, label in configs:
        try:
            params = dict(model=m, messages=messages, **kwargs)
            params = _sanitize_params_for_model(m, params)
            response = c.chat.completions.create(**params)
            return response.choices[0].message
        except Exception as e:
            logger.warning("[%s] 同步 LLM 调用失败: %s", label, e)
            last_err = e
    raise last_err
