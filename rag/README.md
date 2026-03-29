# RAG-4-nutrimaster

植物营养代谢基因问答系统 - 基于 Jina 向量检索 + LLM 生成的 RAG 系统

## 项目简介

基于 98 篇营养代谢相关生物文献的基因信息问答系统，支持智能检索和来源标注。

**核心功能：**
- 🔍 智能基因信息检索 (Jina Embedding v3)
- 🎯 精准结果重排 (Jina Reranker v2)
- 🤖 AI 生成式问答 (GPT-5.4)
- 📚 来源标注 (文章名 + 基因名)
- 💬 流式输出界面
- 📝 会话历史管理

## 系统架构

```
数据加载 (data_loader.py)
    ↓
向量索引构建 (retriever.py - Jina Embedding)
    ↓
查询处理:
  1. 向量召回 top-20 (Jina Embedding v3)
  2. 重排精选 top-10 (Jina Reranker v2)
    ↓
答案生成 (generator.py - GPT-5.4)
    ↓
Web 界面 (Flask + SSE)
```

## 目录结构

```
rag/
├── config.py              # 配置文件
├── data_loader.py         # 数据加载器
├── retriever.py           # 检索器 (Jina)
├── generator.py           # 生成器 (LLM)
├── main.py               # 命令行入口
├── translate.json        # 字段翻译映射
├── requirements.txt      # 依赖
├── data/                 # 文献数据 (*.json)
├── index/                # 向量索引
│   ├── chunks.pkl
│   └── embeddings.npy
└── web/                  # Web 应用
    ├── app.py
    ├── requirements.txt
    ├── run.sh
    ├── run_prod.sh
    └── static/
        ├── index.html
        ├── app.js
        └── style.css
```

## 快速开始

### 1. 安装依赖

```bash
cd rag
pip install -r requirements.txt

# Web 应用依赖
cd web
pip install -r requirements.txt
```

### 2. 配置 API

编辑 `rag/config.py` 或设置环境变量：

```python
API_KEY = "your-llm-api-key"
BASE_URL = "https://ai.gpugeek.com/v1"
LLM_MODEL = "Vendor2/GPT-5.4"

JINA_API_KEY = "your-jina-api-key"
```

### 3. 构建索引

```bash
cd rag
python main.py --rebuild-index
```

### 4. 启动系统

**命令行模式：**

```bash
# 交互模式
python main.py -i

# 单次查询
python main.py -q "MYB65 基因的功能是什么？"
```

**Web 界面：**

```bash
cd web

# 开发模式
python app.py
# 或
bash run.sh

# 生产模式 (Gunicorn)
bash run_prod.sh
```

访问：http://localhost:5000

## 使用示例

### 命令行查询

```bash
$ python main.py -q "植物中DREB转录因子如何调控抗旱性？"

检索到 10 个相关文献

相关文献:
  1. [Plant Cell | DREB1A] (相关度: 0.892)
  2. [Molecular Plant | DREB2] (相关度: 0.845)
  ...

答案:
--------------------------------------------------------------------------------
DREB转录因子在植物抗旱性调控中发挥关键作用...

[Plant Cell | DREB1A] 研究表明，DREB1A 通过结合 DRE/CRT 顺式作用元件...
[Molecular Plant | DREB2] 发现 DREB2 在干旱胁迫下诱导表达...
```

### Web 界面查询

访问 http://localhost:5000，在输入框中输入问题，系统会：

1. 实时流式显示答案
2. 自动标注来源 `[文章名 | 基因名]`
3. 展示参考文献列表
4. 保存查询历史

## 检索配置

在 `config.py` 中调整：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `EMBEDDING_MODEL` | jina-embeddings-v3 | 向量模型 |
| `RERANK_MODEL` | jina-reranker-v2-base-multilingual | 重排模型 |
| `TOP_K_RETRIEVAL` | 20 | 初始召回数量 |
| `TOP_K_RERANK` | 10 | Rerank 后保留数量 |

## 数据格式

输入数据为 JSON 格式，每个文件包含：

```json
{
  "Title": "文章标题",
  "Journal": "期刊名",
  "DOI": "DOI",
  "Pathway_Genes": [...],
  "Regulation_Genes": [...],
  "Common_Genes": [...]
}
```

每个基因包含 37+ 字段，详见 `translate.json`。

## 部署到云服务器

### 1. 克隆到服务器

```bash
git clone https://github.com/captwg/RAG-4-nutrimaster.git
cd RAG-4-nutrimaster
```

### 2. 安装依赖

```bash
pip install -r rag/requirements.txt
pip install -r rag/web/requirements.txt
```

### 3. 配置环境变量

```bash
export API_KEY="your-api-key"
export JINA_API_KEY="your-jina-key"
```

### 4. 构建索引

```bash
cd rag
python main.py --rebuild-index
```

### 5. 启动服务

```bash
cd web
bash run_prod.sh
```

### 6. 使用 Nginx 反向代理（可选）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;  # 重要：支持 SSE
    }
}
```

## 技术栈

- **后端框架**: Flask
- **向量检索**: Jina Embeddings v3
- **结果重排**: Jina Reranker v2
- **LLM**: GPT-5.4 (via gpugeek API)
- **前端**: 原生 HTML/CSS/JavaScript + SSE
- **部署**: Gunicorn

## API 接口

### POST /api/query

查询接口，返回 SSE 流：

**请求：**
```json
{
  "query": "问题文本"
}
```

**响应（SSE）：**
```javascript
// 检索结果
data: {"type": "sources", "data": [...]}

// 答案文本（流式）
data: {"type": "text", "data": "文本片段"}

// 完成
data: {"type": "done"}

// 错误
data: {"type": "error", "data": "错误信息"}
```

### GET /api/health

健康检查

## 常见问题

**Q: 索引构建很慢？**
A: 首次构建需要为所有基因生成向量，大约需要 5-10 分钟。后续启动会自动加载已有索引。

**Q: 如何更新数据？**
A: 将新的 JSON 文件放入 `rag/data/` 目录，然后运行 `python main.py --rebuild-index`。

**Q: Web 界面无法连接？**
A: 检查防火墙设置，确保 5000 端口开放。云服务器需配置安全组规则。

**Q: 流式输出卡顿？**
A: 使用 Nginx 反向代理时，确保设置 `proxy_buffering off;`。

## License

MIT

## 致谢

- Jina AI for embedding and reranker models
- gpugeek for LLM API service
