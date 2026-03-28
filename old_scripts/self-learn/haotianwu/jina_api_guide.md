#+Jina API 使用指南

API Key: `jina_b35345d44f0549f0bcbdb74506012b54XYwaGnqmUbC0t1hSVMX1Flvuji1H`

---

## 一、API 概览

Jina 提供以下核心 API，统一基础 URL 为 `https://api.jina.ai`：

| API | 端点 | 用途 |
|-----|------|------|
| Reader API | `https://r.jina.ai/{url}` | 将网页转为 LLM 友好的 Markdown |
| Search API | `https://s.jina.ai/{query}` | 网页搜索，返回 LLM 友好文本 |
| Embeddings API | `https://api.jina.ai/v1/embeddings` | 文本/图片转向量 |
| Reranker API | `https://api.jina.ai/v1/rerank` | 对搜索结果重排序 |
| Classifier API | `https://api.jina.ai/v1/classify` | 文本/图片分类 |
| Segmenter API | `https://api.jina.ai/v1/segment` | 文本分词和分段 |
| DeepSearch | `https://deepsearch.jina.ai/v1/chat/completions` | 深度搜索推理 |

---

## 二、认证方式

所有 API 请求都在 Header 中携带 API Key：

```bash
-H "Authorization: Bearer jina_b35345d44f0549f0bcbdb74506012b54XYwaGnqmUbC0t1hSVMX1Flvuji1H"
```

---

## 三、Reader API（网页转 Markdown）

将任意 URL 转换为 LLM 可读的 Markdown，直接在 URL 前加 `r.jina.ai/`。

### 基本用法

```bash
# GET 方式（最简单）
curl "https://r.jina.ai/https://example.com" \
  -H "Authorization: Bearer jina_b35345d44f0549f0bcbdb74506012b54XYwaGnqmUbC0t1hSVMX1Flvuji1H"

# 返回 JSON 格式
curl "https://r.jina.ai/https://example.com" \
  -H "Authorization: Bearer jina_b35345d44f0549f0bcbdb74506012b54XYwaGnqmUbC0t1hSVMX1Flvuji1H" \
  -H "Accept: application/json"

# 返回纯文本
curl "https://r.jina.ai/https://example.com" \
  -H "Authorization: Bearer jina_b35345d44f0549f0bcbdb74506012b54XYwaGnqmUbC0t1hSVMX1Flvuji1H" \
  -H "Accept: text/plain"
```

### Python 示例

```python
import requests

url = "https://r.jina.ai/https://example.com"
headers = {
    "Authorization": "Bearer jina_b35345d44f0549f0bcbdb74506012b54XYwaGnqmUbC0t1hSVMX1Flvuji1H",
    "Accept": "application/json"
}
response = requests.get(url, headers=headers)
print(response.json())
```

### 常用请求头参数

| Header | 说明 | 示例值 |
|--------|------|--------|
| `X-Engine` | 浏览器引擎（影响质量/速度） | `browser` / `fast` |
| `X-Return-Format` | 返回格式 | `markdown` / `html` / `text` |
| `X-Timeout` | 超时秒数 | `30` |
| `X-Token-Budget` | 最大 token 限制 | `10000` |
| `X-Remove-Selector` | 移除指定 CSS 元素 | `nav,footer,.sidebar` |
| `X-Target-Selector` | 只提取指定 CSS 元素 | `article,.main-content` |
| `X-No-Gfm-Images` | 移除所有图片 | `true` |

### 计费
- 按**输出 token 数**计费
- 免费版：20 RPM；付费版：500~5000 RPM

---

## 四、Search API（网页搜索）

在查询词前加 `s.jina.ai/` 即可搜索网页，返回 5 条 LLM 友好结果。

### 基本用法

```bash
# GET 方式
curl "https://s.jina.ai/jina+embeddings+api+tutorial" \
  -H "Authorization: Bearer jina_b35345d44f0549f0bcbdb74506012b54XYwaGnqmUbC0t1hSVMX1Flvuji1H" \
  -H "Accept: text/plain"

# JSON 格式
curl "https://s.jina.ai/what+is+RAG" \
  -H "Authorization: Bearer jina_b35345d44f0549f0bcbdb74506012b54XYwaGnqmUbC0t1hSVMX1Flvuji1H" \
  -H "Accept: application/json"
```

### Python 示例

```python
import requests

query = "Jina embeddings tutorial"
url = f"https://s.jina.ai/{query.replace(' ', '+')}"
headers = {
    "Authorization": "Bearer jina_b35345d44f0549f0bcbdb74506012b54XYwaGnqmUbC0t1hSVMX1Flvuji1H",
    "Accept": "application/json"
}
response = requests.get(url, headers=headers)
results = response.json()
for item in results["data"]:
    print(item["title"], item["url"])
    print(item["content"][:200])
```

### 计费
- 每次搜索固定消耗 **10,000 tokens**
- 免费版不可用；付费版：100~1000 RPM

---

## 五、Embeddings API（文本/图片转向量）

### 可用模型

| 模型 | 特点 | 维度 | 上下文 |
|------|------|------|--------|
| `jina-embeddings-v4` | 多模态（文本+图片+PDF），旗舰版 | 128~2048 | 32K |
| `jina-embeddings-v3` | 多语言，支持 89 种语言 | 32~1024 | 8K |
| `jina-embeddings-v5-text-small` | 小型多语言，SOTA | 1024 | 32K |
| `jina-embeddings-v5-text-nano` | 极小型多语言 | 768 | 8K |
| `jina-clip-v2` | 文本+图片，89 种语言 | 512~1024 | 8K |

### 文本 Embedding

```bash
curl https://api.jina.ai/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer jina_b35345d44f0549f0bcbdb74506012b54XYwaGnqmUbC0t1hSVMX1Flvuji1H" \
  -d '{
    "model": "jina-embeddings-v3",
    "input": ["Hello world", "你好世界"],
    "task": "retrieval.passage"
  }'
```

### Python 示例（文本）

```python
import requests

url = "https://api.jina.ai/v1/embeddings"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer jina_b35345d44f0549f0bcbdb74506012b54XYwaGnqmUbC0t1hSVMX1Flvuji1H"
}
data = {
    "model": "jina-embeddings-v3",
    "input": ["你好", "Hello"],
    "task": "retrieval.passage",  # 可选
    "normalized": True             # L2 归一化，用于余弦相似度
}
response = requests.post(url, headers=headers, json=data)
embeddings = response.json()["data"]
for item in embeddings:
    print(f"index={item['index']}, vector_dim={len(item['embedding'])}")
```

### `task` 参数说明（v3/v4）

| task 值 | 适用场景 |
|---------|---------|
| `retrieval.query` | 搜索时的**查询词** |
| `retrieval.passage` | 被检索的**文档段落** |
| `text-matching` | 语义相似度计算 |
| `classification` | 文本分类 |
| `separation` | 聚类任务 |

### 图片 Embedding（v4/clip-v2）

```python
data = {
    "model": "jina-clip-v2",
    "input": [
        {"url": "https://example.com/image.jpg"},  # URL方式
        {"bytes": "<base64_encoded_image>"}          # base64方式
    ]
}
```

---

## 六、Reranker API（重排序）

对初步检索结果按相关性重新排序，显著提升 RAG 精度。

### 可用模型

| 模型 | 特点 | 上下文 |
|------|------|--------|
| `jina-reranker-v3` | 0.6B，131K 上下文，listwise | 131K |
| `jina-reranker-m0` | 多模态，29 种语言 | - |
| `jina-reranker-v2-base-multilingual` | 100+ 语言，支持 function calling | 8K |
| `jina-colbert-v2` | 后期交互，高精度 | 8K |

### 使用示例

```bash
curl https://api.jina.ai/v1/rerank \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer jina_b35345d44f0549f0bcbdb74506012b54XYwaGnqmUbC0t1hSVMX1Flvuji1H" \
  -d '{
    "model": "jina-reranker-v3",
    "query": "植物次生代谢物的生物合成",
    "documents": [
      "黄酮类化合物是植物中重要的次生代谢物...",
      "光合作用是植物的主要能量来源...",
      "花青素的生物合成需要多种酶的参与..."
    ],
    "top_n": 2
  }'
```

### Python 示例

```python
import requests

url = "https://api.jina.ai/v1/rerank"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer jina_b35345d44f0549f0bcbdb74506012b54XYwaGnqmUbC0t1hSVMX1Flvuji1H"
}
data = {
    "model": "jina-reranker-v3",
    "query": "your search query",
    "documents": ["doc1", "doc2", "doc3"],
    "top_n": 3,  # 返回前N个结果
    "return_documents": True  # 是否在结果中返回文档内容
}
response = requests.post(url, headers=headers, json=data)
results = response.json()["results"]
for r in results:
    print(f"score={r['relevance_score']:.4f}: {r['document']['text'][:50]}")
```

---

## 七、Classifier API（分类）

### Zero-shot 分类（无需训练）

```python
import requests

url = "https://api.jina.ai/v1/classify"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer jina_b35345d44f0549f0bcbdb74506012b54XYwaGnqmUbC0t1hSVMX1Flvuji1H"
}
data = {
    "model": "jina-embeddings-v3",
    "input": [{"text": "This is a sports article"}],
    "labels": ["sports", "politics", "technology", "entertainment"]
}
response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### Few-shot 分类（需先训练）

```python
# 第一步：训练分类器
train_url = "https://api.jina.ai/v1/train"
train_data = {
    "model": "jina-embeddings-v3",
    "input": [
        {"text": "I love this product!", "label": "positive"},
        {"text": "This is terrible.", "label": "negative"},
        # 推荐 200-400 个样本
    ]
}
train_resp = requests.post(train_url, headers=headers, json=train_data)
classifier_id = train_resp.json()["classifier_id"]

# 第二步：使用分类器
classify_data = {
    "classifier_id": classifier_id,
    "input": [{"text": "This product is amazing!"}]
}
resp = requests.post(url, headers=headers, json=classify_data)
print(resp.json())
```

---

## 八、Segmenter API（文本分段）

将长文本分割为适合 embedding 的小块，不计入 token 用量。

```python
import requests

url = "https://api.jina.ai/v1/segment"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer jina_b35345d44f0549f0bcbdb74506012b54XYwaGnqmUbC0t1hSVMX1Flvuji1H"
}
data = {
    "content": "Your long text here...",
    "return_tokens": False,
    "return_chunks": True,
    "max_chunk_length": 1000  # 每块最大 token 数
}
response = requests.post(url, headers=headers, json=data)
chunks = response.json()["chunks"]
```

---

## 九、MCP 集成

直接将 Jina 作为 MCP server 使用：

```
mcp.jina.ai
```

添加到你的 MCP 配置后，LLM 可以直接调用 Jina 的 Reader、Search 等功能。

---

## 十、速率限制

| API | 免费版 | Tier 1 | Tier 2（付费高级） |
|-----|--------|--------|--------------------|
| Reader (r.jina.ai) | 20 RPM | 500 RPM | 5000 RPM |
| Search (s.jina.ai) | 不可用 | 100 RPM | 1000 RPM |
| Embeddings | 不可用 | 100 RPM + 100K TPM | 500 RPM + 2M TPM |
| Reranker | 不可用 | 100 RPM + 100K TPM | 500 RPM + 2M TPM |

响应头包含限制信息：`X-RateLimit-Remaining-Requests`、`X-RateLimit-Remaining-Tokens`

---

## 十一、常见错误码

| 错误码 | HTTP | 说明 |
|--------|------|------|
| `AUTH_MISSING_API_KEY` | 401 | 未提供 API Key |
| `AUTH_INVALID_API_KEY` | 401 | API Key 无效 |
| `AUTHZ_INSUFFICIENT_BALANCE` | 403 | 余额不足 |
| `RATE_REQUEST_LIMIT_EXCEEDED` | 429 | 请求频率超限 |
| `RATE_TOKEN_LIMIT_EXCEEDED` | 429 | Token 用量超限 |
| `SERVICE_TIMEOUT` | 504 | 请求超时 |

---

## 十二、RAG 工作流示例

典型的 RAG 管线（Reader + Embeddings + Reranker）：

```python
import requests

API_KEY = "jina_b35345d44f0549f0bcbdb74506012b54XYwaGnqmUbC0t1hSVMX1Flvuji1H"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Step 1: 用 Reader 抓取网页内容
page = requests.get(
    "https://r.jina.ai/https://en.wikipedia.org/wiki/RAG",
    headers={"Authorization": f"Bearer {API_KEY}"}
).text

# Step 2: 用 Segmenter 分块
segments = requests.post(
    "https://api.jina.ai/v1/segment",
    headers=HEADERS,
    json={"content": page, "return_chunks": True, "max_chunk_length": 500}
).json()["chunks"]

# Step 3: 用 Embeddings 向量化（存入向量数据库）
embeddings_resp = requests.post(
    "https://api.jina.ai/v1/embeddings",
    headers=HEADERS,
    json={"model": "jina-embeddings-v3", "input": segments, "task": "retrieval.passage"}
).json()

# Step 4: 用 Reranker 对检索结果重排序
query = "What is retrieval-augmented generation?"
reranked = requests.post(
    "https://api.jina.ai/v1/rerank",
    headers=HEADERS,
    json={"model": "jina-reranker-v3", "query": query, "documents": segments[:20], "top_n": 5}
).json()["results"]
```

---

**官方文档**：https://api.jina.ai/scalar  
**OpenAPI Schema**：https://api.jina.ai/openapi.json
