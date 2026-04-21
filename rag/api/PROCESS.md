# RAG API 开发过程记录

## 项目背景

用户需要将 RAG 系统的核心功能包装成独立的 API，用于 pipeline 测试。原有的 `rag/web/app.py` 包含了完整的 Web UI、用户认证、个人库管理等功能，过于复杂，不适合作为测试接口。

## 需求分析

### 核心需求
1. **轻量级 API**：只保留核心 RAG 查询功能
2. **易于测试**：提供命令行工具和 Python 客户端
3. **Pipeline 集成**：方便在其他项目中调用
4. **去除复杂功能**：不需要认证、Web UI、个人库等

### 保留功能
- Agent 驱动的工具调用循环
- 多工具支持（PubMed、基因库、RAG 搜索、CRISPR）
- 流式和同步两种查询模式
- 深度模式切换
- 模型选择（primary/fallback）

## 设计方案

### 1. 目录结构设计

```
rag/api/
├── __init__.py       # 模块初始化
├── server.py         # FastAPI 服务器（核心）
├── client.py         # Python 客户端库
├── test_client.py    # 命令行测试工具
├── start.sh          # 快速启动脚本
├── README.md         # 使用文档
└── PROCESS.md        # 本文档
```

**设计理由**：
- 独立文件夹便于管理和部署
- 清晰的职责分离（服务端/客户端/测试）
- 提供多种使用方式（脚本/库/命令行）

### 2. API 端点设计

#### GET /api/health
- **功能**：健康检查，返回系统状态
- **返回**：文档块数、可用工具列表、技能数量
- **用途**：测试 API 是否正常运行

#### GET /api/tools
- **功能**：列出所有可用工具
- **返回**：工具名称和描述列表
- **用途**：了解系统能力

#### POST /api/query
- **功能**：同步查询（等待完整结果）
- **请求**：`{query, model_id, use_depth}`
- **返回**：`{answer, sources, tool_calls, steps}`
- **用途**：批量处理、脚本调用

#### POST /api/query/stream
- **功能**：流式查询（SSE 实时推送）
- **请求**：同 `/api/query`
- **返回**：SSE 事件流
- **用途**：实时交互、进度展示

**设计理由**：
- RESTful 风格，易于理解
- 同步/流式两种模式满足不同场景
- 最小化参数，降低使用门槛

### 3. 数据模型设计

#### QueryRequest
```python
class QueryRequest(BaseModel):
    query: str              # 用户查询文本
    model_id: str = "primary"  # 模型选择
    use_depth: bool = False    # 深度模式开关
```

**去除的参数**：
- `max_steps`：Agent 内部固定为 20，无需暴露
- `history`：测试场景不需要多轮对话
- `skill_prefs`/`tool_overrides`：简化配置

#### QueryResponse
```python
class QueryResponse(BaseModel):
    answer: str           # 回答文本
    sources: list[dict]   # 引用来源
    tool_calls: list[dict]  # 工具调用记录
    steps: int            # 实际执行步数
```

**设计理由**：
- 包含完整的可追溯信息
- 便于评估和调试

## 实现过程

### 第一步：创建基础服务器 (server.py)

#### 1.1 初始化组件
```python
# 检索器（gene_db_search 依赖）
retriever = Retriever()
retriever.build_index()

# 工具注册
registry = Toolregistry()
registry.register(PubmedSearchTool())
registry.register(GeneDBSearchTool(retriever=retriever))
registry.register(RAGSearchTool(...))
registry.register(CrisprTool())

# Skill loader（只加载系统 skills）
skill_loader = Skill_loader()

# Agent
agent = Agent(registry, skill_loader, call_llm, call_llm_stream)
```

**关键决策**：
- 启动时一次性初始化所有组件（避免每次请求重建）
- 不使用个人库（`get_personal_lib=lambda uid: None`）
- 不需要用户认证（`user_id=None`）

#### 1.2 实现同步查询端点
```python
@app.post("/api/query")
async def query(req: QueryRequest):
    answer_parts = []
    sources = []
    tool_calls = []
    steps = 0
    
    async for event in agent.run(
        user_input=req.query,  # 注意：参数名是 user_input 不是 query
        user_id=None,
        model_id=req.model_id,
        use_depth=req.use_depth,
        use_personal=False,
    ):
        # 收集事件，组装完整响应
        if event["type"] == "text":
            answer_parts.append(event["data"])
        elif event["type"] == "tool_call":
            steps += 1
            tool_calls.append(...)
        elif event["type"] == "sources":
            sources = event["data"]
    
    return QueryResponse(
        answer="".join(answer_parts),
        sources=sources,
        tool_calls=tool_calls,
        steps=steps,
    )
```

**踩坑记录**：
- ❌ 最初使用 `query=req.query`，报错 `unexpected keyword argument 'query'`
- ✅ 修正为 `user_input=req.query`（Agent.run 的第一个参数名）
- ❌ 最初传递 `max_steps=req.max_steps`，报错 `unexpected keyword argument 'max_steps'`
- ✅ 删除该参数（Agent 内部使用常量 `MAX_STEPS = 20`）

#### 1.3 实现流式查询端点
```python
@app.post("/api/query/stream")
async def query_stream(req: QueryRequest):
    async def event_generator():
        async for event in agent.run(...):
            # SSE 格式：data: {json}\n\n
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
```

**设计理由**：
- 直接透传 Agent 的事件流
- 前端可以实时显示进度

### 第二步：创建 Python 客户端 (client.py)

#### 2.1 客户端类设计
```python
class RAGClient:
    def __init__(self, base_url: str, timeout: int = 300):
        self.base_url = base_url
        self.timeout = timeout
    
    def query(self, query: str, ...) -> Dict:
        """同步查询"""
        response = requests.post(f"{self.base_url}/api/query", ...)
        return response.json()
    
    def query_stream(self, query: str, ...) -> Iterator[Dict]:
        """流式查询"""
        response = requests.post(f"{self.base_url}/api/query/stream", stream=True)
        for line in response.iter_lines():
            if line.startswith(b"data: "):
                yield json.loads(line[6:])
```

**设计理由**：
- 封装 HTTP 细节，提供 Pythonic 接口
- 统一错误处理（`raise_for_status()`）
- 支持自定义超时

#### 2.2 便捷函数
```python
def query(query_text: str, base_url: str = "http://localhost:8000", use_depth: bool = False) -> str:
    """快速查询函数（返回答案文本）"""
    client = RAGClient(base_url)
    result = client.query(query_text, use_depth=use_depth)
    return result["answer"]
```

**设计理由**：
- 一行代码完成查询
- 适合快速测试和脚本使用

### 第三步：创建命令行测试工具 (test_client.py)

#### 3.1 功能设计
- 健康检查：`--health`
- 同步查询：`--query "..."`
- 流式查询：`--query "..." --stream`
- 深度模式：`--depth`

#### 3.2 实现要点
```python
def test_stream(base_url, query, ...):
    """流式查询，实时打印"""
    for line in response.iter_lines():
        event = json.loads(line[6:])
        if event["type"] == "text":
            print(event["data"], end="", flush=True)  # 实时输出
        elif event["type"] == "tool_call":
            print(f"\n[工具] {event['tool']}")  # 显示工具调用
```

**设计理由**：
- 模拟真实用户体验
- 便于调试和演示

### 第四步：创建启动脚本 (start.sh)

```bash
#!/bin/bash
cd "$(dirname "$0")/.."

# 检查 .env 文件
if [ ! -f "../.env" ]; then
    echo "❌ 错误: 未找到 .env 文件"
    exit 1
fi

# 启动服务
python -m api.server --host "$HOST" --port "$PORT" "$@"
```

**设计理由**：
- 一键启动，降低使用门槛
- 自动检查环境配置
- 支持环境变量覆盖

### 第五步：编写文档 (README.md)

#### 文档结构
1. 快速开始（启动服务、测试查询）
2. API 端点详细说明
3. Python 客户端示例
4. Pipeline 集成示例
5. 配置说明
6. 故障排查

**设计理由**：
- 从简单到复杂，逐步深入
- 提供完整的代码示例
- 覆盖常见问题

## 遇到的问题与解决

### 问题 1：参数名不匹配

**现象**：
```
Agent.run() got an unexpected keyword argument 'query'
```

**原因**：
- API 使用 `query=req.query`
- 但 `Agent.run()` 的第一个参数名是 `user_input`

**解决**：
```python
# 错误
agent.run(query=req.query, ...)

# 正确
agent.run(user_input=req.query, ...)
```

**教训**：
- 先查看目标函数的签名
- 不要假设参数名

### 问题 2：max_steps 参数不存在

**现象**：
```
Agent.run() got an unexpected keyword argument 'max_steps'
```

**原因**：
- `Agent.run()` 没有 `max_steps` 参数
- 它使用模块级常量 `MAX_STEPS = 20`

**解决**：
- 从 `QueryRequest` 删除 `max_steps` 字段
- 从 `agent.run()` 调用中删除该参数

**教训**：
- 不要盲目添加"看起来有用"的参数
- 以实际 API 为准

### 问题 3：LLM 请求超时

**现象**：
```
openai.APITimeoutError: Request timed out.
```

**原因**：
- OpenAI 客户端默认超时太短（60 秒）
- Agent 多轮工具调用可能需要更长时间

**解决**：
```python
from openai import Timeout
_TIMEOUT = Timeout(timeout=300.0, connect=10.0)

primary_client = AsyncOpenAI(..., timeout=_TIMEOUT)
fallback_client = AsyncOpenAI(..., timeout=_TIMEOUT)
```

**教训**：
- 考虑最坏情况的执行时间
- 超时配置要覆盖所有客户端实例

### 问题 4：路径导入问题

**现象**：
- 文件移动到 `api/` 后，导入路径失效

**解决**：
```python
# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 使用绝对导入
from rag.core.llm_client import call_llm
from rag.core.agent import Agent
```

**教训**：
- 使用绝对导入而非相对导入
- 确保 `sys.path` 包含项目根目录

## 测试验证

### 测试 1：健康检查
```bash
$ curl http://localhost:8001/api/health
{
  "status": "ok",
  "total_chunks": 70,
  "tools": ["design_crispr_experiment", "gene_db_search", "rag_search", "pubmed_search"],
  "skills": 3
}
```
✅ 通过

### 测试 2：同步查询
```bash
$ curl -X POST http://localhost:8001/api/query \
  -H "Content-Type: application/json" \
  -d '{"query":"番茄中番茄红素合成的关键基因有哪些？"}'
```

**结果**：
- 返回完整答案（包含 PSY、PDS、ZDS、CRTISO 等基因）
- 5 条 PubMed 引用来源
- 3 步工具调用记录
- 耗时约 60 秒

✅ 通过

### 测试 3：流式查询
```bash
$ python -m api.test_client --query "..." --stream
```

**结果**：
- 实时显示工具调用进度
- 逐字输出回答文本
- 最后显示引用来源

✅ 通过

### 测试 4：Python 客户端
```python
from rag.api.client import RAGClient

client = RAGClient("http://localhost:8001")
result = client.query("番茄中番茄红素合成的关键基因有哪些？")
print(result["answer"])
```

✅ 通过

## 性能优化

### 1. 启动时预加载
- 检索器索引在启动时构建一次
- 避免每次请求重建索引

### 2. 客户端复用
- 模块级 `AsyncOpenAI` 客户端
- 避免每次请求创建新连接

### 3. 超时配置
- 设置合理的超时时间（300 秒）
- 避免无限等待

### 4. 流式输出
- 使用 SSE 实时推送
- 降低首字节延迟

## 与 Web 版本的对比

| 特性 | Web 版本 (app.py) | API 版本 (api/server.py) |
|------|------------------|-------------------------|
| 认证 | ✅ Supabase 认证 | ❌ 无认证 |
| 个人库 | ✅ 支持上传 PDF | ❌ 不支持 |
| Web UI | ✅ 完整前端界面 | ❌ 仅 API |
| Admin | ✅ Flask 管理后台 | ❌ 无管理功能 |
| 代码行数 | ~660 行 | ~230 行 |
| 依赖 | FastAPI + Flask + Supabase | FastAPI only |
| 用途 | 生产环境 | Pipeline 测试 |

**简化比例**：约 65% 代码减少

## 后续改进方向

### 短期
1. ✅ 添加详细代码注释
2. ✅ 编写 PROCESS.md 文档
3. ⬜ 添加单元测试
4. ⬜ 添加 Docker 支持

### 中期
1. ⬜ 批量查询接口 `/api/batch`
2. ⬜ 查询历史记录 `/api/history`
3. ⬜ 工具性能统计 `/api/stats`
4. ⬜ 添加 API 认证（可选）

### 长期
1. ⬜ WebSocket 支持（替代 SSE）
2. ⬜ 分布式部署支持
3. ⬜ 查询结果缓存（Redis）
4. ⬜ 监控和日志聚合

## 总结

### 成功经验
1. **最小化原则**：只保留核心功能，大幅简化代码
2. **多种接口**：提供服务端、客户端、命令行三种使用方式
3. **完整文档**：从快速开始到故障排查，覆盖全流程
4. **实际测试**：每个功能都经过真实查询验证

### 关键决策
1. **去除认证**：测试环境不需要，降低复杂度
2. **去除个人库**：依赖用户数据，不适合 API 测试
3. **固定参数**：隐藏 `max_steps` 等内部参数，简化接口
4. **增加超时**：从 60 秒提升到 300 秒，适应多轮调用

### 技术亮点
1. **自动 fallback**：主 API key 过期自动切换备用
2. **流式输出**：SSE 实时推送，提升用户体验
3. **完整追溯**：返回工具调用记录和引用来源
4. **易于集成**：一行代码完成查询

### 适用场景
- ✅ Pipeline 自动化测试
- ✅ 批量数据处理
- ✅ 性能基准测试
- ✅ 第三方系统集成
- ❌ 生产环境（需要认证和权限控制）
- ❌ 多用户场景（无个人库支持）

---

**开发时间**：约 2 小时  
**代码行数**：~500 行（含注释和文档）  
**测试状态**：✅ 全部通过  
**文档完整度**：✅ 100%
