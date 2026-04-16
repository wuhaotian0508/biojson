"""
RAG 系统全局配置

所有模块共享的配置项，包括：
  - 路径配置（数据目录、索引目录）
  - Jina API 配置（嵌入、重排序）
  - LLM API 配置（生成、翻译、基因提取）
  - 检索参数（top-k、chunk 大小）
  - PubMed 联网搜索配置
  - 个人知识库配置
  - Supabase 认证配置
  - Web 服务配置

配置优先级：环境变量 > .env 文件 > 代码默认值
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# ---- 加载 .env 文件中的环境变量 ----
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env", override=True)

# ===== 路径配置 =====
BASE_DIR = Path(__file__).resolve().parent.parent.parent    # 项目根目录 (biojson/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent       # rag/ 目录本身
DATA_DIR = BASE_DIR / "data"               # 基因 JSON 数据目录
INDEX_DIR = BASE_DIR / "rag" / "index"     # 向量索引存储目录

# ===== Jina API 配置（嵌入向量 + 重排序） =====
JINA_API_KEY = os.getenv("JINA_API_KEY", "")
JINA_EMBEDDING_URL = "https://api.jina.ai/v1/embeddings"   # 嵌入向量 API 端点
JINA_RERANK_URL = "https://api.jina.ai/v1/rerank"          # 重排序 API 端点

# ===== LLM API 配置（OpenAI 兼容格式） =====
LLM_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_BASE_URL = os.getenv("OPENAI_BASE_URL")
LLM_MODEL = os.getenv("MODEL", "Vendor2/GPT-5.4")

# ===== Fallback LLM API 配置（主 API 被内容过滤时自动切换） =====
FALLBACK_API_KEY  = os.getenv("FALLBACK_API_KEY")
FALLBACK_BASE_URL = os.getenv("FALLBACK_BASE_URL")
FALLBACK_MODEL    = os.getenv("FALLBACK_MODEL")

# ===== 检索参数 =====
EMBEDDING_MODEL = "jina-embeddings-v3"                        # Jina 嵌入模型
RERANK_MODEL = "jina-reranker-v2-base-multilingual"           # Jina 多语言重排序模型
TOP_K_RETRIEVAL = 20   # 普通模式：向量检索召回数量（第一阶段粗排）
TOP_K_RERANK = 10      # 普通模式：重排序后保留数量（第二阶段精排）

# ===== 深度调研模式参数 =====
DEEP_TOP_K_RETRIEVAL = 40   # 深度模式：召回更多候选
DEEP_TOP_K_RERANK = 20      # 深度模式：保留更多精排结果
CHUNK_SIZE = 1500            # 文本切片大小（字符数）
CHUNK_OVERLAP = 200          # 相邻切片重叠（字符数），避免跨切片信息丢失

# ===== PubMed 联网搜索配置 =====
PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
PUBMED_MAX_RESULTS = 10  # 每次搜索最大返回文献数

# ===== 个人知识库配置 =====
PERSONAL_LIB_DIR = PROJECT_ROOT / "personal_lib"  # 个人库根目录
MAX_PDF_SIZE_MB = 50    # 单个 PDF 最大体积（MB）
MAX_FILES_PER_USER = 20 # 每用户最多上传文件数

# ===== Supabase 认证配置 =====
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_ANON_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
SITE_URL = os.getenv("SITE_URL", "")  # 部署后的实际访问地址，用于邮箱验证跳转

# ===== 邮件发送配置（163 SMTP） =====
SMTP_HOST = "smtp.163.com"
SMTP_PORT = 465
SMTP_USER = os.getenv("SMTP_USER", "nutrimaster@163.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_NAME = "NutriMaster"

# ===== Web 服务配置 =====
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "5000"))
ADMIN_PORT = int(os.getenv("ADMIN_PORT", "5501"))
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")


# ===== 模型选项列表（从 .env 动态构建，供前端 API 下拉框使用） =====
def _build_model_options() -> list[dict]:
    options = []
    if LLM_API_KEY:
        options.append({
            "id": "primary",
            "name": os.getenv("MODEL_NAME", LLM_MODEL),
            "model": LLM_MODEL,
            "api_key": LLM_API_KEY,
            "base_url": LLM_BASE_URL,
        })
    if FALLBACK_API_KEY:
        options.append({
            "id": "fallback",
            "name": os.getenv("FALLBACK_MODEL_NAME", FALLBACK_MODEL or "Fallback"),
            "model": FALLBACK_MODEL,
            "api_key": FALLBACK_API_KEY,
            "base_url": FALLBACK_BASE_URL,
        })
    # 支持 MODEL_2_*, MODEL_3_* 等扩展
    i = 2
    while os.getenv(f"MODEL_{i}_KEY"):
        options.append({
            "id": f"model_{i}",
            "name": os.getenv(f"MODEL_{i}_NAME", f"Model {i}"),
            "model": os.getenv(f"MODEL_{i}_MODEL"),
            "api_key": os.getenv(f"MODEL_{i}_KEY"),
            "base_url": os.getenv(f"MODEL_{i}_URL"),
        })
        i += 1
    return options

MODEL_OPTIONS = _build_model_options()


def require_setting(name: str, value: str) -> str:
    """
    验证必需配置项是否已设置。

    参数:
        name:  配置项名称（仅用于错误消息）
        value: 配置项的值

    返回:
        原样返回 value

    异常:
        ValueError: 当 value 为空字符串或 None 时
    """
    if value:
        return value
    raise ValueError(f"Missing required setting: {name}")
