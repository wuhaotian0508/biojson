"""
配置文件 - RAG 系统配置
"""
import os
from pathlib import Path

# 项目路径
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
INDEX_DIR = PROJECT_ROOT / "index"
WEB_DIR = PROJECT_ROOT / "web"

# API 配置
API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "https://api.gpugeek.com/v1")  # 注意是 api 不是 ai
LLM_MODEL = os.getenv("LLM_MODEL", "Vendor2/GPT-5.4")

# Jina API 配置
JINA_API_KEY = os.getenv("JINA_API_KEY", "")

# 检索配置
EMBEDDING_MODEL = "jina-embeddings-v3"
RERANK_MODEL = "jina-reranker-v2-base-multilingual"
TOP_K_RETRIEVAL = 20  # 初始召回数量
TOP_K_RERANK = 10     # Rerank 后保留数量

# 向量维度
EMBEDDING_DIM = 1024

# 系统提示词
SYSTEM_PROMPT = """你是一个专业的植物营养代谢基因问答助手。你的任务是根据提供的文献信息回答用户关于基因的问题。

回答要求：
1. 基于检索到的文献信息进行回答，不要编造信息
2. 每条信息都要标注来源，格式为：[文章名 | 基因名]
3. 如果文献中没有相关信息，请明确告知用户
4. 回答要专业、准确、简洁
5. 如果涉及多个基因，请分点说明
"""

# Web 配置
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
