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
BASE_DIR = Path(os.getenv("BASE_DIR", EXTRACTOR_DIR.parent))
PROMPTS_DIR = EXTRACTOR_DIR / "prompts"
INPUT_DIR = Path(os.getenv("MD_DIR", EXTRACTOR_DIR / "input"))
OUTPUT_DIR = Path(os.getenv("JSON_DIR", EXTRACTOR_DIR / "output"))
REPORTS_DIR = Path(os.getenv("REPORTS_DIR", EXTRACTOR_DIR / "reports"))
TOKEN_USAGE_DIR = Path(os.getenv("TOKEN_USAGE_DIR", EXTRACTOR_DIR / "reports" / "token-usage"))
PROCESSED_DIR = Path(os.getenv("PROCESSED_DIR", INPUT_DIR / "processed"))

PROMPT_PATH = Path(os.getenv("PROMPT_PATH", PROMPTS_DIR / "nutri_gene_prompt_v4.txt"))
SCHEMA_PATH = Path(os.getenv("SCHEMA_PATH", PROMPTS_DIR / "nutri_gene_schema_v4.json"))

# ─── API configuration ───────────────────────────────────────────────────────
MODEL = os.getenv("MODEL", "Vendor2/Claude-4.6-opus")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "")

# ─── Concurrency ─────────────────────────────────────────────────────────────
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "10"))


_primary_client = None
_fallback_client = None
_fallback_resolved = False


def get_openai_client():
    """Return the primary OpenAI-compatible client (cached)."""
    global _primary_client
    if _primary_client is None:
        _primary_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )
    return _primary_client


def get_fallback_client():
    """Return the fallback client (cached), or None if not configured."""
    global _fallback_client, _fallback_resolved
    if not _fallback_resolved:
        key = os.getenv("FALLBACK_API_KEY")
        url = os.getenv("FALLBACK_BASE_URL")
        if key and url:
            _fallback_client = OpenAI(api_key=key, base_url=url)
        _fallback_resolved = True
    return _fallback_client


def ensure_dirs():
    """Create all required output directories."""
    for d in [OUTPUT_DIR, REPORTS_DIR, TOKEN_USAGE_DIR, PROCESSED_DIR]:
        d.mkdir(parents=True, exist_ok=True)
