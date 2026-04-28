"""
config.py — Centralized configuration for the extractor pipeline.

All paths, API settings, and concurrency settings.

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
EXTRACTOR_MODEL = os.getenv("EXTRACTOR_MODEL", "")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# ─── Concurrency ─────────────────────────────────────────────────────────────
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "10"))


_primary_client = None


def get_openai_client():
    """获取 extraction 专用 OpenAI 客户端（单例缓存）。"""
    global _primary_client
    if _primary_client is None:
        _primary_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )
    return _primary_client


def ensure_dirs():
    """创建所有必需的输出目录（输出、报告、token 用量、已处理）。

    在 pipeline 启动时调用一次，确保目录存在。
    """
    for d in [OUTPUT_DIR, REPORTS_DIR, TOKEN_USAGE_DIR, PROCESSED_DIR]:
        d.mkdir(parents=True, exist_ok=True)
