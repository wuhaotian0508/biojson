"""
工具调用钩子 - 记录所有工具调用和返回结果

提供统一的日志记录接口，用于追踪 Agent 的工具调用行为。
日志文件：rag/logs/tool_calls.log
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

# 获取日志目录
_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

# 创建专用的工具调用日志记录器
tool_call_logger = logging.getLogger("rag.tool_calls")
tool_call_logger.setLevel(logging.INFO)
tool_call_logger.propagate = False  # 不传播到父 logger

# 文件处理器
_file_handler = logging.FileHandler(
    _LOG_DIR / "tool_calls.log",
    encoding="utf-8",
    mode="a"
)
_file_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
)
tool_call_logger.addHandler(_file_handler)


def log_tool_call(tool_name: str, args: dict[str, Any], user_id: str | None = None):
    """记录工具调用开始

    Args:
        tool_name: 工具名称
        args: 工具参数
        user_id: 用户 ID（可选）
    """
    log_entry = {
        "event": "tool_call",
        "tool": tool_name,
        "args": args,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
    }
    tool_call_logger.info(json.dumps(log_entry, ensure_ascii=False))


def log_tool_result(
    tool_name: str,
    result: Any,
    success: bool = True,
    error: str | None = None,
    user_id: str | None = None,
):
    """记录工具调用结果

    Args:
        tool_name: 工具名称
        result: 工具返回结果
        success: 是否成功
        error: 错误信息（如果失败）
        user_id: 用户 ID（可选）
    """
    # 截断过长的结果（保留前 2000 字符）
    result_str = str(result) if result is not None else ""
    if len(result_str) > 2000:
        result_str = result_str[:2000] + f"...(truncated, total {len(result_str)} chars)"

    log_entry = {
        "event": "tool_result",
        "tool": tool_name,
        "success": success,
        "result": result_str,
        "error": error,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
    }
    tool_call_logger.info(json.dumps(log_entry, ensure_ascii=False))


def log_query_optimization(
    tool_name: str,
    original_query: str,
    optimized_query: str,
    user_id: str | None = None,
):
    """记录查询优化

    Args:
        tool_name: 工具名称（如 pubmed_search）
        original_query: 原始查询
        optimized_query: 优化后的查询
        user_id: 用户 ID（可选）
    """
    log_entry = {
        "event": "query_optimization",
        "tool": tool_name,
        "original_query": original_query,
        "optimized_query": optimized_query,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
    }
    tool_call_logger.info(json.dumps(log_entry, ensure_ascii=False))

