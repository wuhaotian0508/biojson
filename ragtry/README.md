# BioJSON RAG 系统

基于 Jina 向量检索 + LLM 生成的基因信息问答系统，支持来源标注（文章名 + 基因名）。

## 项目结构

```
biojson/rag/
├── config.py        # 所有配置项（API、路径、检索参数）
├── data_loader.py   # 数据加载与预处理
├── retriever.py     # Jina 向量检索 + Rerank
├── generator.py     # LLM 生成（带来源标注）
├── main.py          # 主入口
└── index/           # 向量索引缓存（自动生成）
    ├── chunks.pkl       # 基因切片数据
    └── embeddings.npy   # 向量矩阵
```

## 数据流

```
data/*.json                用户Query
    │                          │
    ▼                          ▼
data_loader.py           retriever.py
(100篇论文 → 216个基因chunk)  (Jina Embedding v3 向量召回 top-20)
    │                          │
    ▼                          ▼
index/embeddings.npy     Jina Reranker v2 重排 → top-10
                               │
                               ▼
                         generator.py
                         (LLM 生成答案，每条信息标注来源)
                               │
                               ▼
                         [文章名 | 基因名] 格式的结构化回答
```

## 各模块说明

### config.py
集中管理所有配置，从 `.env` 读取 API 密钥：

| 配置项 | 说明 | 默认值 |
|---|---|---|
| `JINA_API_KEY` | Jina 向量/Rerank API | 从参数传入 |
| `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` | 生成模型 | 读取 `.env` 中的 OPENAI_* |
| `EMBEDDING_MODEL` | 向量模型 | `jina-embeddings-v3` |
| `RERANK_MODEL` | 重排模型 | `jina-reranker-v2-base-multilingual` |
| `TOP_K_RETRIEVAL` | 初始召回数量 | 20 |
| `TOP_K_RERANK` | Rerank 后保留数量 | 10 |

### data_loader.py
- 加载 `data/*.json`（100 篇论文）
- 每个基因生成一个 `GeneChunk`，包含：
  - 可检索文本（核心字段拼接：基因名、物种、表型、机制、通路、互作等）
  - 来源信息（文章标题、期刊、DOI）
  - 完整 metadata（原始 40+ 字段）

### retriever.py
两阶段检索：
1. **向量召回**：用 Jina Embedding v3 计算 query 与所有 chunk 的余弦相似度，取 top-20
2. **Rerank 精排**：用 Jina Reranker v2 对 top-20 重新打分，取 top-10

索引首次构建后缓存到 `index/`，后续直接加载。

### generator.py
- 将检索结果格式化为上下文，发送给 LLM
- System Prompt 要求：
  - 只使用检索到的信息，不编造
  - 每个关键信息标注 `[文章名 | 基因名]`
  - 末尾附完整引用清单
- 支持流式输出

## 使用方法

```bash
cd /data/haotianwu/biojson/rag
```

### 交互模式（推荐）
```bash
python main.py -i
# 或直接
python main.py
```
进入后输入问题即可，输入 `quit` 退出。

### 单次查询
```bash
python main.py -q "植物中DREB转录因子如何调控抗旱性？"
```

### 重建索引
添加新数据到 `data/` 后需要重建：
```bash
python main.py --build-index -i
```

### 其他参数
```bash
python main.py -q "..." --no-rerank    # 跳过 Rerank，只用向量召回
python main.py -q "..." --no-stream    # 关闭流式输出，一次性返回
```

## 输出示例

每个答案包含：
1. **结构化回答** — 分点论述，每点附来源标注
2. **来源标注格式** — `[文章标题 | 基因名]`
3. **引用清单** — 末尾列出所有引用的文章和基因

```
BpNAC090 被定义为第一层 NAC 转录因子，可调控 8 个第二层 TF
[Hierarchical transcription factor and regulatory network for drought
response in Betula platyphylla | BpNAC090]

引用来源清单：
1. Hierarchical transcription factor and regulatory network... | BpNAC090
2. FLS2-RBOHD-PIF4 Module Regulates Plant Response to... | PIF4
...
```

## 依赖

```
pip install openai requests numpy python-dotenv
```
