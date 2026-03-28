"""RAG系统配置"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(Path(__file__).parent.parent / ".env")

# 路径配置
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
INDEX_DIR = BASE_DIR / "rag" / "index"

# Jina API配置
JINA_API_KEY = os.getenv("JINA_API_KEY", "jina_b35345d44f0549f0bcbdb74506012b54XYwaGnqmUbC0t1hSVMX1Flvuji1H")
JINA_EMBEDDING_URL = "https://api.jina.ai/v1/embeddings"
JINA_RERANK_URL = "https://api.jina.ai/v1/rerank"

# LLM API配置
LLM_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_BASE_URL = os.getenv("OPENAI_BASE_URL")
LLM_MODEL = os.getenv("MODEL", "gpt-4o")

# 检索配置
EMBEDDING_MODEL = "jina-embeddings-v3"
RERANK_MODEL = "jina-reranker-v2-base-multilingual"
TOP_K_RETRIEVAL = 20  # 初始检索数量
TOP_K_RERANK = 10     # rerank后保留数量
CHUNK_SIZE = 1500     # 文本切片大小
CHUNK_OVERLAP = 200   # 切片重叠
