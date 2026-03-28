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


def get_openai_client():
    """Create the primary OpenAI-compatible client."""
    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
    )


def get_fallback_client():
    """Create the fallback client, or None if not configured."""
    key = os.getenv("FALLBACK_API_KEY")
    url = os.getenv("FALLBACK_BASE_URL")
    if key and url:
        return OpenAI(api_key=key, base_url=url)
    return None


def ensure_dirs():
    """Create all required output directories."""
    for d in [OUTPUT_DIR, REPORTS_DIR, TOKEN_USAGE_DIR, PROCESSED_DIR]:
        d.mkdir(parents=True, exist_ok=True)
