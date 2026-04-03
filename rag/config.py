"""RAG系统配置"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(Path(__file__).parent.parent / ".env")

# 路径配置
BASE_DIR = Path(__file__).parent.parent
PROJECT_ROOT = Path(__file__).parent  # rag/ 目录本身
DATA_DIR = BASE_DIR / "data"
INDEX_DIR = BASE_DIR / "rag" / "index"

# Jina API配置
JINA_API_KEY = os.getenv("JINA_API_KEY", "")
JINA_EMBEDDING_URL = "https://api.jina.ai/v1/embeddings"
JINA_RERANK_URL = "https://api.jina.ai/v1/rerank"

# LLM API配置
LLM_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_BASE_URL = os.getenv("OPENAI_BASE_URL")
LLM_MODEL = os.getenv("MODEL", "Vendor2/GPT-5.4")

# 检索配置
EMBEDDING_MODEL = "jina-embeddings-v3"
RERANK_MODEL = "jina-reranker-v2-base-multilingual"
TOP_K_RETRIEVAL = 20  # 初始检索数量
TOP_K_RERANK = 10     # rerank后保留数量

# 深度调研配置
DEEP_TOP_K_RETRIEVAL = 40   # 深度模式：初始检索数量
DEEP_TOP_K_RERANK = 20      # 深度模式：rerank保留数量
CHUNK_SIZE = 1500     # 文本切片大小
CHUNK_OVERLAP = 200   # 切片重叠

# 联网搜索配置
PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
PUBMED_MAX_RESULTS = 10

# 个人知识库配置
PERSONAL_LIB_DIR = PROJECT_ROOT / "personal_lib"
MAX_PDF_SIZE_MB = 50
MAX_FILES_PER_USER = 20

# ===== Supabase 配置（新增） =====
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_ANON_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

# Web配置
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "5000"))
ADMIN_PORT = int(os.getenv("ADMIN_PORT", "5501"))
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")


def require_setting(name: str, value: str) -> str:
    """Raise a clear error when an experimental RAG dependency is missing."""
    if value:
        return value
    raise ValueError(f"Missing required setting: {name}")
