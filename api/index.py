"""
Vercel Python Serverless Function — Flask app 入口
将 rag/web/app.py 的 Flask 实例暴露给 Vercel runtime
"""
import sys
from pathlib import Path

# 项目根目录（api/ 的上一级）
ROOT = Path(__file__).resolve().parent.parent

# 添加必要的 import 路径（与 rag/web/app.py 一致）
sys.path.insert(0, str(ROOT / "rag" / "web"))
sys.path.insert(0, str(ROOT / "rag"))
sys.path.insert(0, str(ROOT))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# 导入 Flask app 实例
from app import app

# Vercel 要求导出名为 app 的 WSGI 应用
# （已经是 app 了，无需额外操作）
