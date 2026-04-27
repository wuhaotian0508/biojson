"""
LLM 客户端网关 — 所有 LLM 调用的统一入口

功能：
  1. 主/备自动切换（primary → fallback）
  2. model_id 路由（从 config.MODEL_OPTIONS 动态选择客户端）
  3. 异步调用 call_llm()（支持 tool calling）
  4. 异步流式 call_llm_stream()（逐 chunk yield）
  5. 同步调用 call_llm_sync()（供 CRISPR pipeline 等同步代码使用）

模型差异处理：
  - GPT-5.4: 标准 OpenAI tool calling，支持 temperature 等参数
  - DeepSeek reasoner (V3.2/V4): 支持 tool calling，但需要：
    1. 同一轮工具调用循环内回传 reasoning_content
    2. thinking 模式下 temperature/top_p 等参数被忽略，不传以避免警告
    3. logprobs/top_logprobs 参数会报 400 错误，必须移除
    4. assistant message 需保留 reasoning_content 字段
    5. V4 通过 extra_body 配置 thinking 模式和 reasoning_effort

DeepSeek V4 thinking 配置：
  - thinking.type: "enabled" (默认) | "disabled"
  - reasoning_effort: "high" (默认) | "max" (Agent 复杂任务自动升级)
  - 通过 extra_body 传递（OpenAI SDK 要求）

主/备切换策略：
  - 主 API 失败时自动切换到备用 API
  - 适用场景：内容过滤、限流、服务不可用
  - 备用 API 配置：FALLBACK_API_KEY, FALLBACK_BASE_URL, FALLBACK_MODEL

model_id 路由：
  - 支持动态选择模型（从 config.MODEL_OPTIONS）
  - 前端下拉框选择模型 → 传递 model_id → 自动路由到对应客户端
  - 支持扩展：MODEL_2_*, MODEL_3_* 等环境变量

超时配置：
  - 默认 5 分钟（300 秒）
  - 适配多轮工具调用场景（Agent 可能需要多次 tool calling）
  - 连接超时 10 秒

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

# DeepSeek reasoner 系列模型（V3.2/V4 已支持 tool calling，但参数处理不同）
_DEEPSEEK_REASONER_MODELS = {"deepseek-reasoner", "deepseek-r1", "deepseek-v4"}

# DeepSeek reasoner thinking 模式下会忽略这些参数，主动移除以避免 API 警告
_DEEPSEEK_IGNORED_PARAMS = {"temperature", "top_p", "presence_penalty", "frequency_penalty"}

# DeepSeek reasoner thinking 模式下传这些参数会报 400 错误
_DEEPSEEK_FORBIDDEN_PARAMS = {"logprobs", "top_logprobs"}

# DeepSeek V4 thinking 模式配置（通过 extra_body 传递）
# reasoning_effort: "high" (默认) | "max" (复杂任务)
# thinking.type: "enabled" (默认) | "disabled"
_DEEPSEEK_DEFAULT_THINKING = {"type": "enabled"}
_DEEPSEEK_DEFAULT_EFFORT = "high"  # Agent 复杂任务会自动升级到 "max"


def is_deepseek_reasoner(model_name: str) -> bool:
    """判断是否为 DeepSeek reasoner 系列模型。"""
    name = model_name.lower()
    return any(m in name for m in _DEEPSEEK_REASONER_MODELS)


def _sanitize_params_for_model(model_name: str, params: dict, is_agent_call: bool = False) -> dict:
    """根据模型类型清理不兼容的参数，并添加 DeepSeek V4 thinking 配置。

    Args:
        model_name: 模型名称
        params: API 调用参数字典
        is_agent_call: 是否为 Agent 多轮工具调用（复杂任务，自动使用 max effort）
    """
    if not is_deepseek_reasoner(model_name):
        return params

    # DeepSeek reasoner: 移除 thinking 模式下会忽略或报错的参数
    for key in _DEEPSEEK_IGNORED_PARAMS | _DEEPSEEK_FORBIDDEN_PARAMS:
        params.pop(key, None)

    # DeepSeek V4: 通过 extra_body 配置 thinking 模式
    # 注意：OpenAI SDK 要求 thinking 参数必须通过 extra_body 传递
    extra_body = params.get("extra_body", {})

    # 1. thinking 开关（默认 enabled）
    if "thinking" not in extra_body:
        extra_body["thinking"] = _DEEPSEEK_DEFAULT_THINKING.copy()

    # 2. reasoning_effort（Agent 复杂任务自动升级到 max）
    if "reasoning_effort" not in extra_body:
        effort = "max" if is_agent_call else _DEEPSEEK_DEFAULT_EFFORT
        extra_body["reasoning_effort"] = effort

    if extra_body:
        params["extra_body"] = extra_body

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
async def call_llm(messages, tools=None, model_id: str = "", is_agent_call: bool = False, **kwargs):
    """主+备异步调用。返回 response.choices[0].message。

    支持 model_id 路由：从 MODEL_OPTIONS 动态选择客户端。
    DeepSeek reasoner: 支持 tools，但自动移除 temperature 等不兼容参数。
    DeepSeek V4: 自动配置 thinking 模式和 reasoning_effort。

    Args:
        messages: 对话消息列表（OpenAI 格式: [{role, content}, ...]）
        tools: 工具定义列表（可选，OpenAI function calling 格式）
        model_id: 模型路由 ID
            - "": 使用主模型（primary）
            - "primary": 同上
            - "fallback": 使用备用模型
            - "model_2" 等: 从 config.MODEL_OPTIONS 动态查找
        is_agent_call: 是否为 Agent 多轮工具调用场景
            - True: DeepSeek V4 自动使用 reasoning_effort="max"
            - False: 使用默认 reasoning_effort="high"
        **kwargs: 其他 OpenAI API 参数（temperature, max_tokens 等）
            - DeepSeek reasoner 会自动移除不兼容的参数

    返回:
        response.choices[0].message 对象（包含 content / tool_calls / reasoning_content 等）

    主备切换策略:
        1. 先尝试 model_id 指定的客户端
        2. 失败后自动切换到 fallback 客户端（如果配置且非当前客户端）
        3. 所有客户端均失败则抛出最后一个异常

    异常:
        - 所有客户端均失败时抛出最后一个 Exception
        - 常见: APIError (429/500), APITimeoutError, AuthenticationError
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
            # 根据模型清理不兼容参数，并添加 DeepSeek V4 thinking 配置
            params = _sanitize_params_for_model(m, params, is_agent_call=is_agent_call)
            response = await c.chat.completions.create(**params)
            return response.choices[0].message
        except Exception as e:
            logger.warning("[%s] LLM 调用失败: %s", label, e)
            last_err = e
    raise last_err


# ------------------------------------------------------------------
# 异步流式调用（yield raw chunks）
# ------------------------------------------------------------------
async def call_llm_stream(messages, model_id: str = "", is_agent_call: bool = False, **kwargs):
    """主+备异步流式调用。逐 chunk yield 原始 SSE 对象。

    与 call_llm() 的区别：
      - call_llm() 等待完整响应后返回 message 对象
      - call_llm_stream() 逐 chunk yield，适用于前端实时打字效果

    Args:
        messages: 对话消息列表（OpenAI 格式）
        model_id: 模型路由 ID（同 call_llm）
        is_agent_call: 是否为 Agent 多轮调用（影响 reasoning_effort）
        **kwargs: 其他 API 参数（stream=True 自动添加）

    Yields:
        原始 chunk 对象（ChatCompletionChunk），每个 chunk 包含:
        - choices[0].delta.content: 文本片段（可能为 None）
        - choices[0].delta.tool_calls: 工具调用片段（流式拼接）
        - choices[0].delta.reasoning_content: DeepSeek 推理内容片段

    主备切换策略:
        同 call_llm()，先尝试主客户端，失败后切换到备用客户端。
        注意：流式调用中如果主客户端已开始 yield 后才失败，不会切换到备用
        （因为无法回退已 yield 的 chunk）。实际上失败通常发生在连接阶段。

    异常:
        - 所有客户端均失败时抛出最后一个 Exception
    """
    client, model = _resolve_async_client(model_id)
    configs = [(client, model, "selected")]
    if fallback_client and client is not fallback_client:
        configs.append((fallback_client, FALLBACK_MODEL_NAME, "fallback"))

    last_err = None
    for c, m, label in configs:
        try:
            params = dict(model=m, messages=messages, stream=True, **kwargs)
            params = _sanitize_params_for_model(m, params, is_agent_call=is_agent_call)
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
def call_llm_sync(messages, is_agent_call: bool = False, **kwargs):
    """主+备同步调用。返回 response.choices[0].message。

    与 call_llm() 的区别：
      - call_llm() 是异步函数（async def），需要 await 调用
      - call_llm_sync() 是同步函数（def），直接调用返回结果

    使用场景：
      - 供不支持 async/await 的同步代码使用（如 CRISPR pipeline）
      - 简单脚本、Jupyter notebook 等非异步环境

    Args:
        messages: 对话消息列表（OpenAI 格式）
        is_agent_call: 是否为 Agent 多轮调用（影响 reasoning_effort）
        **kwargs: 其他 API 参数

    返回:
        response.choices[0].message 对象

    主备切换策略:
        同 call_llm()，先尝试主客户端，失败后切换到备用客户端。

    异常:
        - 所有客户端均失败时抛出最后一个 Exception

    注意:
        - 不支持 model_id 路由（始终使用 primary/fallback）
        - 如果需要路由功能，请使用异步版本 call_llm()
    """
        is_agent_call: 是否为 Agent 多轮调用
        **kwargs: 其他 API 参数
    """
    configs = [(primary_sync, PRIMARY_MODEL, "primary")]
    if fallback_sync:
        configs.append((fallback_sync, FALLBACK_MODEL_NAME, "fallback"))

    last_err = None
    for c, m, label in configs:
        try:
            params = dict(model=m, messages=messages, **kwargs)
            params = _sanitize_params_for_model(m, params, is_agent_call=is_agent_call)
            response = c.chat.completions.create(**params)
            return response.choices[0].message
        except Exception as e:
            logger.warning("[%s] 同步 LLM 调用失败: %s", label, e)
            last_err = e
    raise last_err
