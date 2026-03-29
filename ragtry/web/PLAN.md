# RAG 问答 Web 界面实现计划

## 快速开始

**TL;DR** - 为 RAG 系统添加 Web 界面，所有 Web 代码在独立的 `rag/web/` 目录中。

### 快速启动（实现完成后）

```bash
# 1. 安装依赖
cd /data/haotianwu/biojson/rag/web
pip install -r requirements.txt

# 2. 启动服务器
python app.py

# 3. 打开浏览器
# 访问: http://localhost:5000
```

### 文件结构

```
rag/
├── web/                    # 🆕 Web 界面（新增）
│   ├── app.py             # Flask 后端
│   ├── static/
│   │   ├── index.html     # 前端页面
│   │   ├── app.js         # 前端逻辑
│   │   └── style.css      # 样式
│   ├── requirements.txt   # 依赖
│   └── PLAN.md           # 本计划文档
│
├── main.py               # 原有 RAG（不变）
├── retriever.py
├── generator.py          # 新增一个方法
└── ...
```

### 实现步骤总览

1. 创建 `web/` 目录结构
2. 创建 Flask 后端 (`web/app.py`)
3. 修改生成器支持流式输出 (`generator.py`)
4. 创建前端三件套 (HTML/CSS/JS)
5. 添加依赖和启动脚本
6. 测试验证

---

## Context

**背景**：
当前的基因信息 RAG 系统（`/data/haotianwu/biojson/rag/`）仅支持命令行交互式问答。为了更好地演示和使用系统，需要创建一个 Web 界面，使用户可以通过浏览器进行问答，并查看检索来源、历史记录等信息。

**目标**：
实现一个基于 Flask + SSE 流式输出的 Web 问答界面，具有以下特性：
- 交互式问答（输入问题 → 显示答案）
- 流式输出（保留现有 RAG 系统的流式生成体验）
- 显示检索来源（文章名 + 基因名 + 相似度分数）
- 会话历史记录（刷新后不丢失）
- 复制/导出结果
- 清空对话功能
- 极简 UI 风格
- 支持服务器部署

---

## Design

### 1. 整体架构

```
┌─────────────────┐
│   浏览器前端     │  web/static/index.html
│  (HTML/CSS/JS)  │  web/static/style.css
│                 │  web/static/app.js
└────────┬────────┘
         │ HTTP/SSE
         ↓
┌─────────────────┐
│   Flask 后端     │  web/app.py (新增)
│  - 静态文件服务  │
│  - API 端点      │
│  - SSE 流式输出  │
└────────┬────────┘
         │ Python 调用（相对导入）
         ↓
┌─────────────────┐
│   RAG 系统       │  main.py (复用)
│  - GeneRAG 类    │  retriever.py
│  - 检索 + 生成   │  generator.py
└─────────────────┘
```

**文件组织结构**：

```
rag/
├── web/                    # Web 界面目录（新增）
│   ├── app.py             # Flask 应用
│   ├── static/            # 前端静态文件
│   │   ├── index.html
│   │   ├── app.js
│   │   └── style.css
│   ├── requirements.txt   # Web 依赖
│   └── run.sh            # 启动脚本
│
├── main.py               # 原有 RAG 系统
├── retriever.py
├── generator.py
├── data_loader.py
├── config.py
└── ...
```

**设计原则**：
- **隔离性**：所有 Web 相关代码放在 `web/` 子目录
- **不污染原有代码**：RAG 核心代码保持不变
- **相对导入**：Web 应用通过相对导入使用 RAG 组件
- **独立部署**：可以单独运行 `web/app.py`，也可以继续使用 `main.py` 命令行版本

### 2. 后端 API 设计

**Flask 应用 (`rag/app.py`)**：

| 端点 | 方法 | 功能 | 输入/输出 |
|------|------|------|----------|
| `/` | GET | 返回前端页面 | → `static/index.html` |
| `/api/query` | POST | SSE 流式问答 | `{"question": "..."}` → SSE stream |
| `/api/health` | GET | 健康检查 | → `{"status": "ok", "rag_ready": true}` |

**SSE 事件格式**：

```javascript
// 1. 检索来源
event: sources
data: [{"gene": "BpNAC090", "article": "Hierarchical...", "score": 0.95}, ...]

// 2. 流式 token（多次）
event: token
data: {"content": "BpNAC090 被定义为"}

// 3. 完成
event: done
data: {}

// 4. 错误（可选）
event: error
data: {"message": "生成失败"}
```

**关键实现细节**：
- 使用 `flask_cors` 支持跨域
- SSE 通过 `Response` + 生成器函数实现
- Content-Type: `text/event-stream`
- 保持连接，禁用缓冲

### 3. 前端设计

**UI 布局** (极简风格):

```
┌─────────────────────────────────┐
│    基因信息 RAG 问答系统         │  ← 页面标题
├─────────────────────────────────┤
│                                 │
│  ┌────────────────────────────┐│
│  │ Q: 植物中DREB转录因子...    ││  ← 历史对话区
│  │ 检索来源: [3 个基因]        ││  （可滚动）
│  │ A: BpNAC090 被定义为...     ││
│  │    [复制]                   ││
│  └────────────────────────────┘│
│                                 │
│  ┌────────────────────────────┐│
│  │ 生成中... ▌                 ││  ← 正在生成
│  └────────────────────────────┘│
│                                 │
├─────────────────────────────────┤
│ [输入问题...]        [发送]     │  ← 输入区
│ [清空对话] [导出全部]           │  ← 功能按钮
└─────────────────────────────────┘
```

**前端组件** (`static/app.js`):

1. **UI 管理**
   - `renderMessage(role, content, sources)` - 渲染单条消息
   - `appendToken(content)` - 追加流式 token
   - `showLoading() / hideLoading()` - 显示/隐藏加载状态

2. **SSE 客户端**
   - `sendQuestion(question)` - 发起查询
   - 使用 `EventSource` 监听 SSE 事件
   - 处理 `sources`, `token`, `done`, `error` 事件

3. **历史管理**
   - `saveHistory()` - 保存到 `localStorage`
   - `loadHistory()` - 页面加载时恢复
   - 历史格式: `[{q: "...", a: "...", sources: [...]}, ...]`

4. **功能按钮**
   - 复制答案：`navigator.clipboard.writeText()`
   - 清空对话：清除 DOM + localStorage
   - 导出全部：生成 Markdown 文本下载

**样式** (`static/style.css`):
- 配色：白色背景 + 浅灰边框 + 深灰文字
- 等宽字体：基因名用 `font-family: monospace`
- 响应式布局：`max-width: 800px; margin: auto;`
- 流式输出光标：CSS 动画闪烁

### 4. 数据流

```
用户输入问题
    ↓
前端 JS 验证 (非空)
    ↓
POST /api/query {"question": "..."}
    ↓
Flask 接收请求
    ↓
调用 rag.query(question, show_sources=True, stream=True)
    ↓
检索器返回 results: List[(GeneChunk, score)]
    ↓
SSE 发送: event=sources, data=[...]
    ↓
前端显示: "检索到 N 个相关基因"
    ↓
生成器逐 token 输出
    ↓
SSE 发送: event=token, data={"content": "..."}
    ↓
前端实时追加到答案区
    ↓
生成完毕
    ↓
SSE 发送: event=done
    ↓
前端保存到 localStorage
```

### 5. 错误处理

| 错误场景 | 后端处理 | 前端显示 |
|---------|---------|---------|
| 问题为空 | 400 Bad Request | "请输入问题" |
| RAG 未初始化 | 503 Service Unavailable | "系统正在初始化，请稍后重试" |
| API 调用失败 | 500 Internal Server Error | "生成失败：{错误信息}" |
| SSE 连接中断 | - | "连接中断，请重试" |
| 网络超时 | EventSource timeout | "请求超时，请检查网络" |

---

## Implementation Plan

### 步骤 1: 创建 Web 目录结构

**创建目录**:
```bash
mkdir -p /data/haotianwu/biojson/rag/web/static
```

**复制计划文档**:
```bash
cp /home/ubuntu/.claude/plans/giggly-wishing-canyon.md /data/haotianwu/biojson/rag/web/PLAN.md
```

**说明**:
- 创建 `web/` 目录和 `static/` 子目录
- 将本计划文档复制到 `web/PLAN.md`，方便查阅

### 步骤 2: 创建 Flask 后端 (`web/app.py`)

**文件**: `/data/haotianwu/biojson/rag/web/app.py`

**实现内容**:
- 导入 Flask, flask_cors, 以及现有的 RAG 组件
- 初始化 Flask app，配置 static 目录
- 在 app 启动时初始化 GeneRAG 系统（或按需初始化）
- 实现 `/` 路由（返回 `index.html`）
- 实现 `/api/health` 路由（JSON 响应）
- 实现 `/api/query` 路由（SSE 流式输出）
  - 读取请求 JSON
  - 调用检索器和生成器
  - 包装为 SSE 格式发送

**完整代码结构**:
```python
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
import sys
from pathlib import Path

# 导入父目录的 RAG 组件（web/ → rag/）
sys.path.insert(0, str(Path(__file__).parent.parent))
from retriever import JinaRetriever
from generator import RAGGenerator

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# 全局初始化 RAG 系统
print("初始化 RAG 系统...")
retriever = JinaRetriever()
retriever.build_index(force=False)
generator = RAGGenerator()
print("初始化完成！")

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "rag_ready": True})

@app.route('/api/query', methods=['POST'])
def query():
    try:
        data = request.get_json()
        question = data.get('question', '').strip()

        if not question:
            return jsonify({"error": "问题不能为空"}), 400

        def generate():
            try:
                # 1. 检索
                results = retriever.retrieve(question, use_rerank=True)
                sources = [
                    {
                        "gene": chunk.gene_name,
                        "article": chunk.article_title[:50] + "...",
                        "score": float(score)
                    }
                    for chunk, score in results[:5]
                ]
                yield f"event: sources\ndata: {json.dumps(sources, ensure_ascii=False)}\n\n"

                # 2. 流式生成
                for token in generator.generate_stream(question, results):
                    yield f"event: token\ndata: {json.dumps({'content': token}, ensure_ascii=False)}\n\n"

                # 3. 完成
                yield f"event: done\ndata: {{}}\n\n"

            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'message': str(e)}, ensure_ascii=False)}\n\n"

        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
```

**说明**:
- `sys.path.insert(0, str(Path(__file__).parent.parent))` - 将父目录（rag/）加入路径
- 这样可以直接导入 `retriever`, `generator` 等模块
- Web 应用完全独立在 `web/` 目录，不污染原有代码

### 步骤 2: 修改生成器支持流式 yield (`rag/generator.py`)

**文件**: `/data/haotianwu/biojson/rag/generator.py`

**修改内容**:
- 在 `RAGGenerator` 类中添加新方法 `generate_stream()`
- 基于现有的 `generate()` 方法，改为 yield token

**关键代码**:
```python
def generate_stream(self, question: str, results: List[Tuple[GeneChunk, float]]):
    """流式生成答案，逐 token yield"""
    context = self._build_context(results)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"问题：{question}\n\n上下文：\n{context}"}
    ]

    response = requests.post(
        self.base_url + "/chat/completions",
        json={"model": self.model, "messages": messages, "stream": True},
        headers={"Authorization": f"Bearer {self.api_key}"},
        stream=True
    )

    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                chunk = json.loads(data)
                if "choices" in chunk:
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        yield delta["content"]
```

**说明**:
- 复用现有的 `_build_context()` 和 system prompt
- 使用 `requests.post(..., stream=True)` 流式调用 API
- 解析 SSE 格式的 OpenAI API 响应

### 步骤 3: 创建前端 HTML (`web/static/index.html`)

**文件**: `/data/haotianwu/biojson/rag/web/static/index.html`

**结构**:
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>基因信息 RAG 问答系统</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>基因信息 RAG 问答系统</h1>
        </header>

        <div id="chat-container" class="chat-container">
            <!-- 消息动态插入 -->
        </div>

        <div class="input-area">
            <textarea id="question-input" placeholder="输入问题..." rows="2"></textarea>
            <button id="send-btn" class="primary">发送</button>
        </div>

        <div class="actions">
            <button id="clear-btn">清空对话</button>
            <button id="export-btn">导出全部</button>
        </div>
    </div>

    <script src="app.js"></script>
</body>
</html>
```

### 步骤 4: 实现前端逻辑 (`web/static/app.js`)

**文件**: `/data/haotianwu/biojson/rag/web/static/app.js`

**核心功能**:

1. **初始化**
   ```javascript
   document.addEventListener('DOMContentLoaded', () => {
       loadHistory();
       setupEventListeners();
   });
   ```

2. **发送问题 + SSE 接收**
   ```javascript
   function sendQuestion(question) {
       appendMessage('user', question);

       // 使用 fetch + ReadableStream 接收 SSE (支持 POST)
       fetch('/api/query', {
           method: 'POST',
           headers: {'Content-Type': 'application/json'},
           body: JSON.stringify({question: question})
       })
       .then(response => {
           const reader = response.body.getReader();
           const decoder = new TextDecoder();
           let buffer = '';
           let currentAnswer = '';
           let sources = [];

           function processChunk({done, value}) {
               if (done) {
                   saveToHistory(question, currentAnswer, sources);
                   return;
               }

               buffer += decoder.decode(value, {stream: true});
               const lines = buffer.split('\n\n');
               buffer = lines.pop(); // 保留不完整的行

               lines.forEach(line => {
                   if (!line.trim()) return;
                   const [eventLine, dataLine] = line.split('\n');
                   if (!dataLine) return;

                   const event = eventLine.replace('event: ', '');
                   const data = dataLine.replace('data: ', '');

                   if (event === 'sources') {
                       sources = JSON.parse(data);
                       showSources(sources);
                   } else if (event === 'token') {
                       const token = JSON.parse(data).content;
                       currentAnswer += token;
                       updateAnswer(currentAnswer);
                   } else if (event === 'error') {
                       showError(JSON.parse(data).message);
                   }
               });

               return reader.read().then(processChunk);
           }

           return reader.read().then(processChunk);
       })
       .catch(err => showError('请求失败: ' + err.message));
   }
   ```

3. **历史管理**
   ```javascript
   function saveToHistory(question, answer, sources) {
       const history = JSON.parse(localStorage.getItem('rag-history') || '[]');
       history.push({q: question, a: answer, sources: sources, time: new Date()});
       localStorage.setItem('rag-history', JSON.stringify(history));
   }

   function loadHistory() {
       const history = JSON.parse(localStorage.getItem('rag-history') || '[]');
       history.forEach(item => {
           appendMessage('user', item.q);
           appendMessage('assistant', item.a, item.sources);
       });
   }
   ```

4. **导出功能**
   ```javascript
   function exportAll() {
       const history = JSON.parse(localStorage.getItem('rag-history') || '[]');
       const markdown = history.map((item, i) =>
           `## 问题 ${i+1}\n${item.q}\n\n## 答案\n${item.a}\n\n---\n`
       ).join('\n');

       const blob = new Blob([markdown], {type: 'text/markdown'});
       const url = URL.createObjectURL(blob);
       const a = document.createElement('a');
       a.href = url;
       a.download = 'rag-history.md';
       a.click();
   }
   ```

### 步骤 5: 创建样式文件 (`web/static/style.css`)

**文件**: `/data/haotianwu/biojson/rag/web/static/style.css`

**样式要点**:
```css
/* 极简配色 */
:root {
    --bg: #ffffff;
    --border: #e0e0e0;
    --text: #333333;
    --text-light: #666666;
    --primary: #0066cc;
}

/* 布局 */
.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

/* 消息气泡 */
.message {
    margin: 16px 0;
    padding: 12px;
    border-radius: 8px;
}

.message.user {
    background: #f0f0f0;
    text-align: right;
}

.message.assistant {
    background: #f8f8f8;
    border-left: 3px solid var(--primary);
}

/* 基因名样式 */
.gene-name {
    font-family: 'Courier New', monospace;
    background: #e8e8e8;
    padding: 2px 6px;
    border-radius: 3px;
}

/* 流式输出光标 */
.cursor {
    display: inline-block;
    width: 2px;
    height: 1em;
    background: var(--primary);
    animation: blink 1s infinite;
}

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
}
```

### 步骤 6: 创建依赖文件 (`web/requirements.txt`)

**文件**: `/data/haotianwu/biojson/rag/web/requirements.txt`

```
flask==3.0.0
flask-cors==4.0.0
gunicorn==21.2.0
```

**说明**: Web 应用的独立依赖文件

### 步骤 7: 创建启动脚本 (`web/run.sh`)

**文件**: `/data/haotianwu/biojson/rag/web/run.sh`

```bash
#!/bin/bash
# 开发模式运行
cd /data/haotianwu/biojson/rag/web
export FLASK_ENV=development
python app.py
```

**生产部署脚本** (`web/run_prod.sh`):
```bash
#!/bin/bash
# 生产模式运行
cd /data/haotianwu/biojson/rag/web
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 300 app:app
```

---

## Critical Files

### 新增文件

**Web 界面目录** (`/data/haotianwu/biojson/rag/web/`)：

1. **`web/app.py`**
   - Flask 应用主文件
   - 包含所有 API 端点
   - 通过相对导入使用 RAG 组件

2. **`web/static/index.html`**
   - 前端 HTML 结构
   - 极简布局

3. **`web/static/app.js`**
   - 前端 JavaScript 逻辑
   - fetch + ReadableStream 实现 SSE 客户端
   - 历史管理和功能按钮

4. **`web/static/style.css`**
   - 极简样式
   - 响应式布局

5. **`web/requirements.txt`**
   - Web 界面依赖

6. **`web/run.sh`** 和 **`web/run_prod.sh`**
   - 开发和生产启动脚本

### 修改文件

1. **`/data/haotianwu/biojson/rag/generator.py`**
   - 添加 `generate_stream()` 方法
   - 支持逐 token yield
   - 不影响现有 `generate()` 方法

---

## Verification

### 本地测试步骤

1. **安装依赖**
   ```bash
   cd /data/haotianwu/biojson/rag/web
   pip install -r requirements.txt
   ```

2. **启动服务器**
   ```bash
   cd /data/haotianwu/biojson/rag/web
   python app.py
   # 或
   bash run.sh
   ```

   预期输出：
   ```
   初始化 RAG 系统...
   初始化完成！
    * Running on http://127.0.0.1:5000
   ```

3. **打开浏览器**
   ```
   访问: http://localhost:5000
   ```

   验证：
   - ✓ 页面正常加载
   - ✓ 标题显示："基因信息 RAG 问答系统"
   - ✓ 输入框和按钮正常显示

4. **测试问答功能**
   - 输入问题："植物中DREB转录因子如何调控抗旱性？"
   - 点击"发送"

   验证：
   - ✓ 显示"检索到 N 个相关基因"
   - ✓ 答案逐字生成（流式输出）
   - ✓ 显示来源信息（文章名 + 基因名）
   - ✓ 生成完毕后显示"复制"按钮

5. **测试历史记录**
   - 刷新页面

   验证：
   - ✓ 之前的对话仍然显示
   - ✓ 可以继续提问

6. **测试功能按钮**
   - 点击"复制"按钮
     - ✓ 答案已复制到剪贴板
   - 点击"导出全部"
     - ✓ 下载 `rag-history.md` 文件
   - 点击"清空对话"
     - ✓ 所有消息清空
     - ✓ localStorage 清空

7. **测试错误处理**
   - 发送空问题
     - ✓ 显示"请输入问题"
   - 断开网络后提问
     - ✓ 显示"连接中断"

### 生产部署测试

1. **使用 Gunicorn 启动**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 --timeout 300 app:app
   ```

2. **测试并发**
   - 打开多个浏览器标签同时提问
   - ✓ 所有请求正常响应

3. **压力测试**（可选）
   ```bash
   # 使用 ab (Apache Bench)
   ab -n 100 -c 10 http://localhost:5000/
   ```

### 健康检查

```bash
curl http://localhost:5000/api/health
```

预期输出：
```json
{"status": "ok", "rag_ready": true}
```

---

## Notes

- **隔离性设计**：所有 Web 相关代码在 `rag/web/` 独立目录中
- **不污染原有代码**：RAG 核心系统保持完全不变（除了 generator.py 添加一个新方法）
- **相对导入**：Web 应用通过 `sys.path` 访问父目录的 RAG 模块
- **独立运行**：可以单独运行 `web/app.py`，也可以继续使用 `main.py` 命令行版本
- **前端无打包**：使用原生 JavaScript，无需 Node.js 或构建工具
- **SSE 流式传输**：使用 fetch + ReadableStream 支持 POST 请求的 SSE
- **本地存储**：历史记录存储在浏览器 localStorage，无需数据库
- **生产部署建议**：使用 Nginx 反向代理 + Gunicorn
