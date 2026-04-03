# BioJSON

植物营养代谢基因结构化提取流水线。从 MinerU 转换的论文 Markdown 中，通过两阶段 LLM 调用（提取 + 验证），输出可复查的结构化 JSON。

---

## 项目架构

```
论文 PDF
    ↓  (MinerU 转换)
extractor/input/*.md
    ↓  API #1: extract_paper()
    │  Title / Journal / DOI + gene arrays + gene_dict
    ↓  API #2+: verify_paper()
    │  字段级验证 + 修正（每 10-12 个基因一批）
extractor/output/*_verified.json
    ↓
rag/data/          ← RAG 系统数据源（实验模块）
    ↓
rag/web/app.py     ← 检索问答 Web 界面（端口 5000）
```

管理后台（端口 5001）提供完整的流水线生命周期管理：上传 zip → 预览首篇 → 批量处理 → 自动重建 RAG 索引。

---

## 目录结构

```
biojson/
├── extractor/                    # 主流水线（正式模块）
│   ├── input/                    # 待处理 Markdown 文件
│   │   └── processed/            # 已归档（处理完毕）的 Markdown
│   ├── output/                   # 最终 verified JSON 输出
│   ├── reports/                  # 每篇论文的提取/验证报告 + token 用量
│   │   └── token-usage/          # token 用量 JSON 文件
│   ├── prompts/                  # Prompt 模板和 JSON Schema
│   │   ├── nutri_gene_prompt_v5.txt
│   │   └── nutri_gene_schema_v5.json
│   ├── pipeline.py               # 编排入口（并行 + 顺序两种模式）
│   ├── extract.py                # 提取阶段��API 调用 #1）
│   ├── verify.py                 # 验证阶段（API 调用 #2+，动态分批）
│   ├── config.py                 # 集中配置（路径、API、并发）
│   ├── text_utils.py             # Markdown 预处理 / LLM section 过滤
│   ├── token_tracker.py          # Token 用量追踪
│   ├── utils.py                  # 共享工具函数
│   ├── __main__.py               # python -m extractor.pipeline 入口
│   └── run.sh                    # 推荐运行入口
│
├── rag/                          # 检索问答模块（实验性）
│   ├── data/                     # verified JSON 数据（RAG 数据源）
│   ├── index/                    # Jina 向量索引（embeddings.npy）
│   ├── web/                      # Flask Web 界面（端口 5000）
│   │   ├── app.py                # Flask 后端 + Supabase 认证
│   │   ├── auth.py               # 认证中间件
│   │   ├── static/               # 前端静态文件
│   │   └── run.sh / run_prod.sh  # 启动脚本
│   ├── main.py                   # CLI 入口（交互 / 单次查询）
│   ├── retriever.py              # Jina 向量检索 + rerank
│   ├── generator.py              # LLM 答案生成
│   ├── build_index.py            # 构建向量索引
│   ├── data_loader.py            # JSON 数据加载与切片
│   ├── online_search.py          # PubMed 联网检索（可选）
│   ├── personal_lib.py           # 个人知识库（PDF 上传）
│   ├── config.py                 # RAG 配置（检索参数、API）
│   └── requirements.txt
│
├── admin/                        # Web 管理后台（端口 5001）
│   ├── app.py                    # Flask 后端（SSE + 流水线管理）
│   ├── run.sh                    # 启动脚本
│   ├── README.md                 # Admin 详细使用说明
│   └── static/                   # SPA 前端（5 个 Tab）
│       ├── index.html
│       ├── style.css             # 深色 lab-console 主题
│       └── admin.js              # 认证、上传、SSE、Prompt 编辑器
│
├── data/                         # 基础 JSON 数据（114 个文件，RAG 数据源）
├── .env                          # 环境变量（不提交 git）
├── .env.example                  # 配置模板
└── README.md
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install openai python-dotenv pytest
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，至少填写主 API 配置：

```env
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
MODEL=Vendor2/Claude-4.6-opus

# 可选：备用 API（主 API 被拦截时自动切换）
FALLBACK_API_KEY=
FALLBACK_BASE_URL=
FALLBACK_MODEL=
```

### 3. 放入论文文件

将 MinerU 转换好的 `.md` 文件放入 `extractor/input/`。

### 4. 运行流水线

```bash
bash extractor/run.sh
```

---

## 运行命令

### extractor 流水线

```bash
bash extractor/run.sh                     # 完整流水线（默认）
bash extractor/run.sh pipeline            # 同上
bash extractor/run.sh pipeline-test       # 测试：处理第 1 个文件
bash extractor/run.sh pipeline-test 3     # 测试：处理第 3 个文件
bash extractor/run.sh pipeline-test name  # 测试：按文件名关键字匹配
bash extractor/run.sh rerun               # 强制重跑全部文件

# 直接调用 Python 模块
python -m extractor.pipeline
python -m extractor.pipeline --test 1
python -m extractor.pipeline --workers 5
```

### RAG 系统（实验）

```bash
# CLI 交互模式
python rag/main.py

# CLI 单次查询
python rag/main.py -q "水稻中调控铁含量的基因有哪些？"

# Web 界面（端口 5000）
cd rag/web && bash run.sh
```

### Admin Panel

```bash
bash admin/run.sh          # 启动管理后台（端口 5001）
```

访问 `http://localhost:5001`，使用 `.env` 中 `ADMIN_EMAIL` 指定的邮箱登录。

---

## 输出文件

| 文件 | 说明 |
|------|------|
| `extractor/output/*_verified.json` | 最终修正后的结构化结果（主产出） |
| `extractor/reports/<paper>/extraction.json` | 原始提取结果 |
| `extractor/reports/<paper>/verification.json` | 字���级验证报告 |
| `extractor/reports/<paper>/gene_dict.json` | 基因字典 |
| `extractor/reports/token-usage/*.json` | Token 用量报告 |

流水线重跑时明确区分三种状态：
- `processed`：本次真正执行并产出结果
- `skipped`：已有 verified 结果，未重复处理
- `failed`：本次执行失败

---

## 模块说明

### extractor（主流水线）

两阶段处理：

1. **提取阶段**（`extract.py`）：API 调用 #1，从论文 Markdown 提取 Title / Journal / DOI + 所有基因信息，输出 gene arrays 和 gene_dict。
2. **验证阶段**（`verify.py`）：API 调用 #2+，对每个基因字段逐一验证（每批 10-12 个基因，动态分批），应用修正后输出最终 JSON。

`pipeline.py` 通过 `ThreadPoolExecutor` 并行处理多篇论文，默认 20 个 worker。

### rag（实验模块）

基于 Jina 向量检索 + LLM 生成的问答系统。数据源为 `rag/data/*.json`（与 `extractor/output/` 格式独立）。支持 PubMed 联网检索和个人 PDF 知识库。

> 注意：RAG 模块当前不直接读取 `extractor/output/*.json`，若要接入主线需先做 schema 适配。

### admin（管理后台）

5-Tab SPA 管理界面：
- **Dashboard**：查看 input 队列、已处理数、归档数
- **Upload**：上传含 `.md` 文件的 zip，自动去重
- **Pipeline**：预览首篇 / 批量处理，SSE 实时进度，完成后自动重建 RAG 索引
- **Papers**：浏览已处理论文列表
- **Prompt / Schema Editor**：在线编辑 `nutri_gene_prompt_v5.txt` 和 `nutri_gene_schema_v5.json`

详细说明见 [`admin/README.md`](./admin/README.md)。

---

## 测试

```bash
pytest -q
python -m compileall extractor rag
```

---

## 配置参考

所有配置项均可通过环境变量覆盖：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENAI_API_KEY` | — | 主 API Key（必需） |
| `OPENAI_BASE_URL` | — | 主 API Base URL（必需） |
| `MODEL` | `Vendor2/Claude-4.6-opus` | 主模型 |
| `FALLBACK_API_KEY` | — | 备用 API Key（可选） |
| `FALLBACK_MODEL` | — | 备用模型（可选） |
| `MAX_WORKERS` | `20` | 并行 worker 数 |
| `TEMPERATURE` | `0.7` | 生成温度 |
| `MD_DIR` | `extractor/input` | Markdown 输入目录 |
| `JSON_DIR` | `rag/data` | JSON 输出目录 |
| `SUPABASE_URL` | — | Supabase URL（Admin/RAG 认证用） |
| `ADMIN_EMAIL` | — | Admin Panel 允许登录的邮箱 |
