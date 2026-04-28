"""
config.py — Centralized configuration for the extractor pipeline.

All paths, API settings, and concurrency settings.

[PR 改动 by 学长 muskliu - 2026-03-29]
- get_openai_client() 和 get_fallback_client() 改为单例缓存模式
  原来每次调用都会创建新的 OpenAI 实例，现在用模块级变量缓存，避免重复创建
- 新增 _primary_client, _fallback_client, _fallback_resolved 三个模块级变量
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ─── Path configuration ──────────────────────────────────────────────────────
EXTRACTOR_DIR = Path(__file__).parent
BASE_DIR = Path(os.getenv("BASE_DIR", EXTRACTOR_DIR.parents[2]))
PROMPTS_DIR = EXTRACTOR_DIR / "prompts"
INPUT_DIR = Path(os.getenv("MD_DIR", EXTRACTOR_DIR / "input"))
OUTPUT_DIR = Path(os.getenv("JSON_DIR", BASE_DIR / "data" / "corpus"))
REPORTS_DIR = Path(os.getenv("REPORTS_DIR", EXTRACTOR_DIR / "reports"))
TOKEN_USAGE_DIR = Path(os.getenv("TOKEN_USAGE_DIR", EXTRACTOR_DIR / "reports" / "token-usage"))
PROCESSED_DIR = Path(os.getenv("PROCESSED_DIR", INPUT_DIR / "processed"))

PROMPT_PATH = Path(os.getenv("PROMPT_PATH", PROMPTS_DIR / "nutri_gene_prompt_v5.txt"))
SCHEMA_PATH = Path(os.getenv("SCHEMA_PATH", PROMPTS_DIR / "nutri_gene_schema_v5.json"))

# ─── API configuration ───────────────────────────────────────────────────────
MODEL = os.getenv("MODEL", "Vendor2/Claude-4.6-opus")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "")

# ─── Concurrency ─────────────────────────────────────────────────────────────
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "10"))


# [PR 改动] 模块级缓存变量，避免每次调用都创建新的 OpenAI 客户端
_primary_client = None       # 主 API 客户端缓存
_fallback_client = None      # 备用 API 客户端缓存
_fallback_resolved = False   # 标记是否已尝试过创建备用客户端


def get_openai_client():
    """获取主 OpenAI 客户端（单例缓存）。

    [PR 改动] 原来每次调用都 return OpenAI(...)，现在用模块级变量缓存，
    整个进程只创建一次客户端实例，多线程并行处理论文时不会重复创建连接。

    Returns:
        OpenAI: 主 API 客户端实例
    """
    global _primary_client
    if _primary_client is None:
        _primary_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )
    return _primary_client


def get_fallback_client():
    """获取备用 OpenAI 客户端（单例缓存），未配置则返回 None。

    [PR 改动] 同样改为缓存模式。用 _fallback_resolved 标记避免重复检查环境变量。
    即使 FALLBACK_API_KEY 未配置，也只检查一次，后续直接返回 None。

    Returns:
        OpenAI | None: 备用客户端实例，未配置时返回 None
    """
    global _fallback_client, _fallback_resolved
    if not _fallback_resolved:
        key = os.getenv("FALLBACK_API_KEY")
        url = os.getenv("FALLBACK_BASE_URL")
        if key and url:
            _fallback_client = OpenAI(api_key=key, base_url=url)
        _fallback_resolved = True
    return _fallback_client


def ensure_dirs():
    """创建所有必需的输出目录（输出、报告、token 用量、已处理）。

    在 pipeline 启动时调用一次，确保目录存在。
    """
    for d in [OUTPUT_DIR, REPORTS_DIR, TOKEN_USAGE_DIR, PROCESSED_DIR]:
        d.mkdir(parents=True, exist_ok=True)
