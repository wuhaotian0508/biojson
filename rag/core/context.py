"""
ContextManager — 上下文窗口管理（三层防御）

参照 EvoMaster 的 ContextManager，但适配本项目 dict-based messages 格式。

三层防御策略:
  L1 轻量裁剪: tokens >= 80% → 清理旧 tool 输出
  L2 摘要压缩: tokens >= 95% → LLM 生成对话摘要，替换旧消息
  L3 紧急截断: API 报 context overflow → 保留 system + 最近 N 条消息
"""
from __future__ import annotations

import json
import logging
import re
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)

# ---- 常量 ----
MAX_CONTEXT_TOKENS = 128_000      # 模型上下文窗口
RESERVED_OUTPUT_TOKENS = 16_000   # 预留给输出的 token
USABLE_TOKENS = MAX_CONTEXT_TOKENS - RESERVED_OUTPUT_TOKENS

PRUNE_THRESHOLD = 0.80    # L1: 80% 触发轻量裁剪
SUMMARY_THRESHOLD = 0.95  # L2: 95% 触发摘要压缩

PRUNE_PROTECT_RECENT_TURNS = 2   # 保护最近 N 个 user turn
PRUNE_MINIMUM_TOKENS = 5_000     # 至少可释放这么多才执行裁剪

TOOL_OUTPUT_CAP = 15_000         # 单个工具输出最大字符数
SAFETY_MARGIN = 1.05             # token 估算安全系数（+5%）

# L2 摘要的系统提示
_SUMMARY_SYSTEM_PROMPT = """\
你是一个对话摘要助手。请将以下对话压缩为结构化摘要，保留关键信息。"""

_SUMMARY_USER_TEMPLATE = """\
请将以下对话内容压缩为简洁摘要，包含：

1. **用户目标**: 用户想做什么
2. **已完成工作**: 已经调用了什么工具、得到了什么结果
3. **关键发现**: 重要的事实、数据、结论
4. **当前状态**: 对话进行到哪一步了

对话内容：
{conversation}

请用中文输出摘要，控制在 500 字以内。"""

# 检测 API 返回的 context overflow 错误
_OVERFLOW_PATTERNS = [
    re.compile(r"context.{0,20}(length|window|limit|overflow|exceed)", re.I),
    re.compile(r"maximum.{0,20}(token|context)", re.I),
    re.compile(r"too.{0,10}(long|many).{0,10}token", re.I),
    re.compile(r"reduce.{0,20}(prompt|input|context)", re.I),
]


class ContextManager:
    """管理 Agent 对话的上下文窗口，防止超限。

    使用方式：
        ctx = ContextManager()

        # 每次 call_llm 前：
        messages = ctx.prepare(messages, tool_specs)

        # call_llm 成功后（如果有 usage 信息）：
        ctx.update_usage(usage_dict)

        # call_llm 异常时检测是否 overflow：
        if ctx.is_overflow_error(error):
            messages = ctx.emergency_truncate(messages)
    """

    def __init__(
        self,
        max_tokens: int = MAX_CONTEXT_TOKENS,
        reserved_output: int = RESERVED_OUTPUT_TOKENS,
        call_llm_for_summary: Callable[..., Awaitable] | None = None,
    ):
        self.max_tokens = max_tokens
        self.reserved_output = reserved_output
        self.usable = max_tokens - reserved_output
        self._call_llm_for_summary = call_llm_for_summary

        # 上次 API 返回的实际 token 使用量
        self._last_prompt_tokens: int = 0
        self._last_msg_count: int = 0

    # ------------------------------------------------------------------
    # Token 估算
    # ------------------------------------------------------------------
    @staticmethod
    def _estimate_text_tokens(text: str) -> int:
        """字符估算: ~4 字符/token（同 EvoMaster SimpleTokenCounter）"""
        return len(text) // 4 if text else 0

    def _estimate_message_tokens(self, msg: dict) -> int:
        """估算单条消息的 token 数"""
        content = msg.get("content") or ""
        if isinstance(content, list):
            # 多模态消息
            tokens = 0
            for part in content:
                if isinstance(part, dict):
                    if part.get("type") == "text":
                        tokens += self._estimate_text_tokens(part.get("text", ""))
                    elif part.get("type") == "image_url":
                        tokens += 750  # 图片固定估算
                else:
                    tokens += self._estimate_text_tokens(str(part))
            return tokens + 4  # 消息 overhead
        return self._estimate_text_tokens(content) + 4

    def _estimate_messages_tokens(self, messages: list[dict]) -> int:
        """估算消息列表的总 token 数"""
        return sum(self._estimate_message_tokens(m) for m in messages)

    def _estimate_tool_specs_tokens(self, tool_specs: list[dict] | None) -> int:
        """估算工具定义的 token 数"""
        if not tool_specs:
            return 0
        try:
            return self._estimate_text_tokens(json.dumps(tool_specs))
        except Exception:
            return len(tool_specs) * 125  # fallback: ~500 chars per spec

    def estimate_total_tokens(
        self,
        messages: list[dict],
        tool_specs: list[dict] | None = None,
    ) -> int:
        """估算当前上下文的总 token 数（含安全系数）"""
        msg_tokens = self._estimate_messages_tokens(messages)
        spec_tokens = self._estimate_tool_specs_tokens(tool_specs)
        raw = msg_tokens + spec_tokens

        # 如果有上次 API 的实际值，用增量法提高准确性
        if self._last_prompt_tokens > 0 and self._last_msg_count > 0:
            if len(messages) >= self._last_msg_count:
                new_msgs = messages[self._last_msg_count:]
                new_tokens = self._estimate_messages_tokens(new_msgs)
                raw = self._last_prompt_tokens + new_tokens

        return int(raw * SAFETY_MARGIN)

    # ------------------------------------------------------------------
    # L1: 轻量裁剪（清理旧 tool 输出）
    # ------------------------------------------------------------------
    def _prune_old_tool_outputs(self, messages: list[dict]) -> list[dict]:
        """将保护区之外的旧 tool 消息 content 替换为占位符。

        保护区: 最近 PRUNE_PROTECT_RECENT_TURNS 个 user turn 内的所有消息。
        """
        # 找保护区边界：从后往前数 user turn
        protect_from = len(messages)
        user_turns_seen = 0
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "user":
                user_turns_seen += 1
                if user_turns_seen >= PRUNE_PROTECT_RECENT_TURNS:
                    protect_from = i
                    break

        # 计算可释放的 token
        prunable_tokens = 0
        prunable_indices = []
        for i in range(protect_from):
            msg = messages[i]
            if msg.get("role") == "tool":
                content = msg.get("content", "")
                if content and content != "[已清理旧工具输出]":
                    tokens = self._estimate_text_tokens(content)
                    prunable_tokens += tokens
                    prunable_indices.append(i)

        if prunable_tokens < PRUNE_MINIMUM_TOKENS:
            logger.debug("L1 裁剪: 可释放 %d tokens < 最小阈值 %d，跳过",
                         prunable_tokens, PRUNE_MINIMUM_TOKENS)
            return messages

        # 执行裁剪
        result = list(messages)  # shallow copy
        pruned_count = 0
        for i in prunable_indices:
            result[i] = {
                **result[i],
                "content": "[已清理旧工具输出]",
            }
            pruned_count += 1

        logger.info("L1 裁剪: 清理了 %d 条旧 tool 输出，释放约 %d tokens",
                     pruned_count, prunable_tokens)
        return result

    # ------------------------------------------------------------------
    # L2: 摘要压缩（LLM 生成对话摘要）
    # ------------------------------------------------------------------
    async def _summarize_old_context(self, messages: list[dict]) -> list[dict]:
        """用 LLM 将旧消息摘要为结构化总结，保留最近 3 轮对话。

        如果 LLM 摘要失败，降级为 L1 裁剪。
        """
        if not self._call_llm_for_summary:
            logger.warning("L2 摘要: 未配置 call_llm_for_summary，降级为 L1")
            return self._prune_old_tool_outputs(messages)

        # 分离: system_msgs / old_msgs / recent_msgs
        system_msgs = []
        rest_start = 0
        for i, msg in enumerate(messages):
            if msg.get("role") == "system":
                system_msgs.append(msg)
                rest_start = i + 1
            else:
                break

        # 找最近 3 个 user turn 的起始位置
        recent_start = len(messages)
        user_turns_seen = 0
        for i in range(len(messages) - 1, rest_start - 1, -1):
            if messages[i].get("role") == "user":
                user_turns_seen += 1
                if user_turns_seen >= 3:
                    recent_start = i
                    break

        old_msgs = messages[rest_start:recent_start]
        recent_msgs = messages[recent_start:]

        if not old_msgs:
            logger.debug("L2 摘要: 没有旧消息可以压缩")
            return messages

        # 构造摘要输入
        conversation_text = []
        for msg in old_msgs:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if isinstance(content, str) and len(content) > 500:
                content = content[:500] + "..."
            if content and content != "[已清理旧工具输出]":
                conversation_text.append(f"[{role}] {content}")

        if not conversation_text:
            return messages

        try:
            summary_messages = [
                {"role": "system", "content": _SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": _SUMMARY_USER_TEMPLATE.format(
                    conversation="\n".join(conversation_text)
                )},
            ]
            summary_response = await self._call_llm_for_summary(
                summary_messages, temperature=0.1,
            )
            summary_text = summary_response.content.strip()

            if not summary_text:
                raise ValueError("摘要为空")

            logger.info("L2 摘要: 压缩了 %d 条旧消息为摘要（%d chars）",
                        len(old_msgs), len(summary_text))

            # 用摘要替换旧消息
            return (
                system_msgs
                + [
                    {"role": "user", "content": "请总结到目前为止的对话进展。"},
                    {"role": "assistant", "content": summary_text},
                ]
                + recent_msgs
            )

        except Exception as e:
            logger.warning("L2 摘要失败，降级为 L1: %s", e)
            return self._prune_old_tool_outputs(messages)

    # ------------------------------------------------------------------
    # L3: 紧急截断
    # ------------------------------------------------------------------
    @staticmethod
    def emergency_truncate(messages: list[dict], keep_recent: int = 5) -> list[dict]:
        """保留 system 消息 + 最近 keep_recent 条消息。"""
        system_msgs = [m for m in messages if m.get("role") == "system"]
        non_system = [m for m in messages if m.get("role") != "system"]

        # 保留最近的消息，但确保不从 tool 消息开始（需要配对的 assistant）
        kept = non_system[-keep_recent:] if len(non_system) > keep_recent else non_system
        # 调整: 如果第一条是 tool 消息，向前找到配对的 assistant
        while kept and kept[0].get("role") == "tool":
            idx = non_system.index(kept[0])
            if idx > 0:
                kept.insert(0, non_system[idx - 1])
            else:
                break

        result = system_msgs + kept
        logger.warning("L3 紧急截断: 从 %d 条消息截断到 %d 条",
                       len(messages), len(result))
        return result

    # ------------------------------------------------------------------
    # 主入口: prepare
    # ------------------------------------------------------------------
    async def prepare(
        self,
        messages: list[dict],
        tool_specs: list[dict] | None = None,
    ) -> list[dict]:
        """主入口: 估算 token，按需执行 L1/L2 压缩。

        返回（可能被压缩的）消息列表。
        """
        tokens = self.estimate_total_tokens(messages, tool_specs)
        ratio = tokens / self.usable if self.usable > 0 else 0

        logger.debug("上下文: 估算 %d tokens / %d usable (%.0f%%)",
                      tokens, self.usable, ratio * 100)

        if ratio >= SUMMARY_THRESHOLD:
            # L2: 摘要压缩
            logger.info("触发 L2 摘要压缩 (%.0f%% >= %.0f%%)",
                        ratio * 100, SUMMARY_THRESHOLD * 100)
            messages = await self._summarize_old_context(messages)
        elif ratio >= PRUNE_THRESHOLD:
            # L1: 轻量裁剪
            logger.info("触发 L1 轻量裁剪 (%.0f%% >= %.0f%%)",
                        ratio * 100, PRUNE_THRESHOLD * 100)
            messages = self._prune_old_tool_outputs(messages)

        return messages

    # ------------------------------------------------------------------
    # 工具
    # ------------------------------------------------------------------
    def update_usage(self, usage: dict, msg_count: int | None = None):
        """记录 API 返回的实际 token 使用量，用于下次增量估算。"""
        prompt_tokens = usage.get("prompt_tokens", 0)
        if prompt_tokens > 0:
            self._last_prompt_tokens = prompt_tokens
            if msg_count is not None:
                self._last_msg_count = msg_count

    def is_overflow(self, usage: dict) -> bool:
        """根据 API 返回的 usage 判断是否接近溢出。"""
        total = usage.get("total_tokens") or (
            usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
        )
        return total >= self.usable

    @staticmethod
    def is_overflow_error(error: Exception) -> bool:
        """检测异常是否为 context overflow 错误。"""
        error_str = str(error)
        return any(p.search(error_str) for p in _OVERFLOW_PATTERNS)

    @staticmethod
    def cap_tool_output(text: str, limit: int = TOOL_OUTPUT_CAP) -> str:
        """截断过长的工具输出，保留首尾。"""
        if not text or len(text) <= limit:
            return text
        half = limit // 2
        return (
            text[:half]
            + f"\n\n...[已截断，原文 {len(text)} 字符，保留首尾各 {half} 字符]...\n\n"
            + text[-half:]
        )
