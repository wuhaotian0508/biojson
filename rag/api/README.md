# RAG API 使用指南

## 目录结构

```
api/
├── __init__.py       # 模块初始化
├── server.py         # API 服务器
├── client.py         # Python 客户端库
├── test_client.py    # 命令行测试工具
├── start.sh          # 快速启动脚本
└── README.md         # 本文档
```

## 快速开始

### 1. 启动 API 服务

**方式一：使用启动脚本（推荐）**
```bash
cd /data/haotianwu/biojson/rag
./api/start.sh
```

**方式二：直接运行**
```bash
cd /data/haotianwu/biojson/rag
python -m api.server --port 8000
```

可选参数：
- `--host`: 监听地址（默认 0.0.0.0）
- `--port`: 监听端口（默认 8000）
- `--reload`: 开发模式，代码修改自动重载

### 2. 测试 API

#### 健康检查
```bash
python -m api.test_client --health
```

#### 同步查询（等待完整结果）
```bash
python -m api.test_client --query "番茄中番茄红素合成的关键基因有哪些？"
```

#### 流式查询（实时输出）
```bash
python -m api.test_client --query "番茄中番茄红素合成的关键基因有哪些？" --stream
```

#### 深度模式（启用 gene_db_search）
```bash
python -m api.test_client --query "..." --depth
```

## API 端点

### GET /api/health
健康检查，返回系统状态。

**响应示例：**
```json
{
  "status": "ok",
  "total_chunks": 1234,
  "tools": ["pubmed_search", "gene_db_search", "rag_search", "crispr_tool"],
  "skills": 5
}
```

### GET /api/tools
列出所有可用工具。

**响应示例：**
```json
{
  "tools": [
    {
      "name": "pubmed_search",
      "description": "搜索 PubMed 文献数据库"
    },
    ...
  ]
}
```

### POST /api/query
同步查询，等待完整结果后返回。

**请求体：**
```json
{
  "query": "番茄中番茄红素合成的关键基因有哪些？",
  "model_id": "primary",
  "use_depth": false,
  "max_steps": 20
}
```

**响应示例：**
```json
{
  "answer": "番茄中番茄红素合成的关键基因包括...",
  "sources": [
    {
      "title": "Lycopene biosynthesis in tomato",
      "doi": "10.1234/example",
      "journal": "Plant Cell"
    }
  ],
  "tool_calls": [
    {
      "tool": "gene_db_search",
      "args": {"query": "lycopene tomato"}
    }
  ],
  "steps": 3
}
```

### POST /api/query/stream
流式查询，通过 SSE (Server-Sent Events) 实时推送结果。

**请求体：** 同 `/api/query`

**响应格式：** SSE 事件流

```
data: {"type": "tool_call", "tool": "gene_db_search", "args": {...}}

data: {"type": "text", "data": "番茄中"}

data: {"type": "text", "data": "番茄红素"}

data: {"type": "sources", "data": [...]}

data: {"type": "done"}
```

**事件类型：**
- `tool_call`: 工具调用开始
- `tool_result`: 工具返回结果摘要
- `text`: 回答文本片段
- `sources`: 引用来源列表
- `done`: 查询完成
- `error`: 错误信息

## Python 客户端示例

### 使用客户端库（推荐）
```python
from rag.api.client import RAGClient

# 创建客户端
client = RAGClient("http://localhost:8000")

# 同步查询
result = client.query("番茄中番茄红素合成的关键基因有哪些？", use_depth=True)
print(result["answer"])
print(f"引用来源: {len(result['sources'])} 条")

# 流式查询
for event in client.query_stream("..."):
    if event["type"] == "text":
        print(event["data"], end="", flush=True)
```

### 快捷函数
```python
from rag.api.client import query

# 一行代码完成查询
answer = query("番茄中番茄红素合成的关键基因有哪些？")
print(answer)
```

### 原始 requests 调用
```python
import requests

response = requests.post(
    "http://localhost:8000/api/query",
    json={
        "query": "番茄中番茄红素合成的关键基因有哪些？",
        "use_depth": True,
    },
    timeout=300
)

result = response.json()
print(result["answer"])
```

### 流式查询（原始）
```python
import requests
import json

response = requests.post(
    "http://localhost:8000/api/query/stream",
    json={"query": "..."},
    stream=True,
    timeout=300
)

for line in response.iter_lines():
    if line.startswith(b"data: "):
        event = json.loads(line[6:])
        if event["type"] == "text":
            print(event["data"], end="", flush=True)
```

## Pipeline 集成示例

```python
from rag.api.client import RAGClient

client = RAGClient("http://localhost:8000")

# 在 pipeline 中批量查询
queries = [
    "番茄中番茄红素合成的关键基因有哪些？",
    "水稻中控制铁含量的基因有哪些？",
    "小麦中影响维生素E含量的关键酶基因？",
]

for q in queries:
    result = client.query(q, use_depth=True)
    print(f"Q: {q}")
    print(f"A: {result['answer'][:200]}...")
    print(f"   ({result['steps']} 步, {len(result['sources'])} 条来源)")
    print()
```

## 配置说明

API 服务使用 `rag/core/config.py` 中的配置，主要包括：

- **LLM API**: 从 `.env` 读取 `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `MODEL`
- **Jina API**: 从 `.env` 读取 `JINA_API_KEY`（用于嵌入和重排序）
- **数据路径**: `data/` 目录存放基因 JSON 数据
- **索引路径**: `rag/index/` 存放向量索引

确保 `.env` 文件配置正确：
```bash
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.example.com/v1
MODEL=Vendor2/GPT-5.4
JINA_API_KEY=your_jina_key
```

## 与 Web 版本的区别

| 特性 | Web 版本 (app.py) | API 版本 (api_server.py) |
|------|------------------|-------------------------|
| 认证 | ✅ Supabase 认证 | ❌ 无认证 |
| 个人库 | ✅ 支持上传 PDF | ❌ 不支持 |
| Web UI | ✅ 完整前端界面 | ❌ 仅 API |
| Admin | ✅ Flask 管理后台 | ❌ 无管理功能 |
| 用途 | 生产环境 | Pipeline 测试 |

## 故障排查

### API 启动失败
- 检查端口是否被占用：`lsof -i :8000`
- 检查 `.env` 配置是否完整
- 查看日志输出的错误信息

### 查询超时
- 增加 `timeout` 参数（默认 300 秒）
- 检查 LLM API 是否可用
- 减少 `max_steps` 参数

### 工具调用失败
- 检查 Jina API key 是否有效
- 检查 `data/` 目录是否有数据文件
- 查看 API 日志中的详细错误信息

## 性能优化建议

1. **预加载索引**: API 启动时自动加载，无需每次查询重建
2. **并发请求**: 使用 `uvicorn --workers 4` 启动多进程
3. **缓存**: 考虑添加 Redis 缓存常见查询结果
4. **限流**: 生产环境建议添加 rate limiting

## 后续扩展

可以基于此 API 添加：
- 批量查询接口 `/api/batch`
- 查询历史记录 `/api/history`
- 工具性能统计 `/api/stats`
- WebSocket 支持（替代 SSE）
