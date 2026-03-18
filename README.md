# BioJSON

基于 LLM 的植物营养代谢基因文献结构化提取管道（Pipeline）+ Web 标注平台。

从科学文献（Markdown 格式）中自动提取关键基因信息为结构化 JSON，并通过 LLM 二次验证消除幻觉（Hallucination），确保提取结果忠实于原文。提供 Web 可视化界面，供专家在线审核和标注提取结果。

## ✨ 功能特性

### 提取管道（Pipeline）

- **MD → JSON 结构化提取**：使用 LLM Function Calling 按预定义 JSON Schema，从文献中提取作物营养代谢关键基因的详细信息。v2 支持 **4 种提取模板**（Common / Pathway / Regulation / Multiple），LLM 自动识别基因功能类别并选择对应模板，Pathway 基因额外提取酶活性和通路定位字段，Regulation 基因额外提取调控机制和靶基因字段
- **幻觉验证与自动修正**：调用 LLM 逐基因、逐字段验证提取结果是否有原文支持，将不支持的字段（UNSUPPORTED）自动修正为 `"NA"`
- **文本预处理**：自动去除论文中的图片、URL、引用列表、致谢等无用内容，减少 Token 消耗
- **增量处理**：自动跳过已处理的文件，支持 `FORCE_RERUN=1` 强制重跑
- **Fallback 机制**：当主 API 因内容审查被拦截时，自动切换到备用 API
- **截断 JSON 自动修复**：当 LLM 输出被截断时，自动修复不完整的 JSON 结构
- **Token 用量追踪**：记录每次 API 调用的 Token 消耗（输入/输出/合计），生成 JSON 格式的用量报告

### Web 标注平台

- **论文列表视图**：展示所有已导入论文，包含标题、期刊、基因数量、验证状态统计
- **论文详情页**：左右分栏布局——左侧展示 Markdown 原文，右侧展示基因提取结果
- **基因卡片**：按 11 个类别分组展示 40+ 个字段，每个字段显示提取值和 AI 自动验证结果
- **专家标注系统**：支持对每个字段进行「✅ 正确 / ❌ 错误 / ✏️ 修改」标注，可填写评论和修正值
- **验证进度条**：可视化展示每篇论文的验证覆盖率（支持/不确定/不支持）
- **技术栈**：Next.js 15 + Supabase + TailwindCSS，支持 Vercel 一键部署

## 📁 项目结构

```
biojson/
├── configs/                    # 配置文件
│   ├── nutri_gene_prompt_v2.txt      #   提取 Prompt v2（基因分类 + 模板选择）
│   ├── nutri_gene_schema_v2.json     #   JSON Schema v2（4 种基因提取模板）
│   └── nutri_gene_schema_base_v2.json #  基础 Schema（公共字段定义）
├── md/                         # 输入：Markdown 格式的科学文献
│   └── processed/              #   验证完成后自动移入的已处理文献
├── json/                       # 输出：验证修正后的最终 JSON
├── reports/                    # 提取结果 + 验证报告（按论文分子目录）
│   └── {paper-dir}/
│       ├── extraction.json     #   LLM 提取的原始 JSON
│       └── verification.json   #   逐字段验证报告
├── token-usage/                # Token 用量报告
├── scripts/                    # 核心脚本
│   ├── run.sh                  #   统一运行入口（配置管理 + 模式选择）
│   ├── md_to_json.py           #   Step 1: MD → JSON 结构化提取
│   ├── verify_response.py      #   Step 2: JSON 幻觉验证与修正
│   ├── text_utils.py           #   文本预处理工具（去图片/URL/引用/致谢）
│   ├── token_tracker.py        #   Token 用量追踪模块
│   ├── import_to_supabase.py   #   数据导入 Supabase 脚本
│   └── dev.sh                  #   本地开发一键启动脚本（端口检测+自动打开浏览器）
├── web/                        # Web 标注平台（Next.js 15）
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx      #     全局布局 + 导航栏
│   │   │   ├── page.tsx        #     首页：论文列表
│   │   │   └── papers/
│   │   │       └── [slug]/
│   │   │           ├── page.tsx        # 论文详情页（服务端）
│   │   │           └── PaperDetail.tsx # 详情交互组件（客户端）
│   │   └── lib/
│   │       ├── supabase.ts     #     Supabase 客户端
│   │       └── types.ts        #     TypeScript 类型定义
│   └── .env.local.example      #     前端环境变量模板
├── database/
│   └── schema.sql              # 数据库建表 SQL（含 RLS 策略）
├── .env                        # 环境变量（API Key 等，不提交到 Git）
├── .env.example                # 环境变量模板
└── .gitignore
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install openai python-dotenv
```

### 2. 配置 API Key

复制环境变量模板并填入实际值：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 主 API
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.gpugeek.com/v1
MODEL=Vendor2/Claude-4.6-opus

# Fallback API（可选，当主 API 因内容审查被拦截时自动切换）
FALLBACK_API_KEY=your-fallback-key-here
FALLBACK_BASE_URL=https://your-fallback-url/v1
FALLBACK_MODEL=volcengine/deepseek-v3-2-251201
```

### 3. 放置文献

将 Markdown 格式的科学文献放入 `md/` 目录。

### 4. 运行

```bash
# 默认模式：提取 + 验证（全量处理所有文献）
bash scripts/run.sh

# 仅提取 MD → JSON
bash scripts/run.sh extract

# 仅验证已有的 JSON
bash scripts/run.sh verify

# 测试模式：仅处理第 1 个文件（提取 + 验证）
bash scripts/run.sh test

# 测试模式：仅处理第 3 个文件
bash scripts/run.sh test 3

# 测试模式：按文件名模糊匹配
bash scripts/run.sh test new

# 强制全部重跑（忽略已有结果）
bash scripts/run.sh rerun

# 强制重跑提取（仅提取阶段）
FORCE_RERUN=1 bash scripts/run.sh extract
```

## 📖 工作流程

```
科学文献 (MD)
      │
      ▼
┌──────────────┐   preprocess_md()    ┌──────────────┐
│  text_utils  │ ─── 去图片/URL/ ───▶ │  清理后文本   │
│              │     引用/致谢         │              │
└──────────────┘                      └──────┬───────┘
                                             │
                                             ▼
┌──────────────┐   Prompt + Schema    ┌──────────────┐
│ md_to_json   │ ── Function Calling ─▶│ extraction   │
│              │     (LLM API)        │    .json      │
└──────────────┘                      └──────┬───────┘
                                             │
                                             ▼
                                  ┌──────────────────┐
                                  │ verify_response   │
                                  │  逐基因逐字段验证  │
                                  │  LLM 二次审查      │
                                  └────────┬─────────┘
                                           │
                                  ┌────────▼─────────┐
                                  │ 修正后的 JSON      │
                                  │ + verification    │
                                  │    .json 报告     │
                                  │ + Token 用量报告   │
                                  └──────────────────┘
                                           │
                                  ┌────────▼─────────┐
                                  │ MD 文件自动移入    │
                                  │ md/processed/     │
                                  └──────────────────┘
```

## ⚙️ 配置说明

### Prompt v2 (`configs/nutri_gene_prompt_v2.txt`)

指导 LLM 进行三步操作：
1. **文献分析 & 核心基因识别**（使用 thinking 工具）：深入阅读文献，判断论文研究的是合成通路还是调控网络，识别核心基因并**分类**为 Pathway（通路酶基因）、Regulation（调控基因）或 Common（通用基因）
2. **结构化信息提取**：根据 Step 1 的分类结果，调用对应模板的 Function Calling 进行提取，遵循「聚焦核心基因」「忠实原文」「标准标识符补充」原则
3. **验证自检**（使用 thinking 工具）：LLM 自我审查提取结果的准确性，发现错误时调用工具修正

### JSON Schema v2 (`configs/nutri_gene_schema_v2.json`)

定义了 **4 种基因提取模板**，根据论文中基因的功能类别自动选择：

| 模板 | 适用场景 | 基因字段 |
|------|---------|---------|
| `CommonGeneExtraction` | 通用基因（非通路酶、非调控） | ~30 个公共字段 |
| `PathwayGeneExtraction` | 代谢通路酶基因 | 公共字段 + 14 个酶/通路专属字段（EC_Number、Catalyzed_Reaction、Biosynthetic_Pathway 等） |
| `RegulationGeneExtraction` | 转录因子/调控基因 | 公共字段 + 14 个调控专属字段（Regulator_Type、Regulation_Mode、Primary_Regulatory_Targets 等） |
| `MultipleGeneExtraction` | 混合类别（同一篇论文含多种类型基因） | 3 个数组：Common_Genes / Pathway_Genes / Regulation_Genes |

**公共字段（~30 个）** 涵盖：物种信息、基因基本信息、代谢产物、表型效应、实验方法、组学数据、遗传变异、育种价值等。

**模板选择逻辑**：
- 论文中所有核心基因都是通路酶 → `PathwayGeneExtraction`
- 论文中所有核心基因都是调控因子 → `RegulationGeneExtraction`
- 论文中所有核心基因都不属于以上两类 → `CommonGeneExtraction`
- 论文中有混合类别的基因 → `MultipleGeneExtraction`

### 文本预处理 (`scripts/text_utils.py`)

对 MinerU 转换的 Markdown 论文进行预处理，减少无用 Token 消耗：
1. **去除图片标签**：CDN 链接和本地路径两种格式
2. **去除 URL 链接**：括号内的 http/https 链接
3. **去除引用列表**：References / Literature Cited 部分
4. **去除致谢段落**：Acknowledgments 部分
5. **合并多余空行**：3 个以上连续空行合并为 2 个

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENAI_API_KEY` | - | 主 API Key（必需） |
| `OPENAI_BASE_URL` | - | 主 API Base URL（必需） |
| `MODEL` | `Vendor2/Claude-4.6-opus` | LLM 模型名称 |
| `TEMPERATURE` | `0.7` | 生成温度 |
| `FALLBACK_API_KEY` | - | 备用 API Key（可选） |
| `FALLBACK_BASE_URL` | - | 备用 API Base URL（可选） |
| `FALLBACK_MODEL` | - | 备用模型名称（可选） |
| `FORCE_RERUN` | - | 设为 `1` 强制重跑，忽略已有结果 |
| `TEST_MODE` | - | 设为 `1` 启用测试模式 |
| `TEST_INDEX` | `1` | 测试模式下处理的文件（编号或文件名） |

## 📊 输出说明

### 提取与验证结果

| 路径 | 说明 |
|------|------|
| `reports/{paper-dir}/extraction.json` | LLM 提取的原始 JSON |
| `reports/{paper-dir}/verification.json` | 逐字段验证报告（SUPPORTED / UNSUPPORTED / UNCERTAIN） |
| `json/{文献名}_nutri_plant_verified.json` | 验证修正后的最终 JSON |

> `{paper-dir}` 命名规则：去掉 `MinerU_markdown_` 前缀，去掉 `_(1)` 后缀，下划线转连字符。
> 例如：`MinerU_markdown_mmc3_2031567019886178304` → `mmc3-2031567019886178304`

### Token 用量报告

| 路径 | 说明 |
|------|------|
| `token-usage/extract-{timestamp}.json` | 提取阶段的 Token 用量 |
| `token-usage/verify-{timestamp}.json` | 验证阶段的 Token 用量 |

### 验证报告结构

验证报告包含逐基因、逐字段的验证结果和修正统计：

```json
{
  "file": "文献名",
  "genes": [
    {
      "gene_name": "ZmPSY1",
      "verification": {
        "Gene_Name": { "verdict": "SUPPORTED", "reason": "..." },
        "EC_Number": { "verdict": "UNSUPPORTED", "reason": "..." }
      },
      "corrections": [
        { "field": "EC_Number", "old_value": "2.5.1.32", "new_value": "NA", "reason": "..." }
      ]
    }
  ],
  "summary": {
    "total_fields": 120,
    "supported": 105,
    "unsupported": 10,
    "uncertain": 5,
    "total_corrections": 10
  }
}
```

## 🔧 高级特性

### 增量处理

默认情况下，Pipeline 会自动跳过已存在结果的文件：
- 提取阶段：跳过已有 `reports/{paper-dir}/extraction.json` 的文件
- 验证阶段：跳过已有 `json/{文献名}_nutri_plant_verified.json` 的文件

设置 `FORCE_RERUN=1` 可强制重新处理所有文件。

### Fallback 机制

当主 API 返回空结果（可能因内容审查拦截）时，Pipeline 会自动切换到备用 API 重试。需要在 `.env` 中配置 `FALLBACK_API_KEY`、`FALLBACK_BASE_URL` 和 `FALLBACK_MODEL`。

### 截断 JSON 自动修复

当 LLM 输出因 `max_tokens` 限制被截断时，提取脚本会尝试：
1. 找到最后一个完整的基因对象
2. 补全缺失的 `]` 和 `}` 括号
3. 尽可能抢救已提取的基因数据

### 测试模式

测试模式支持三种文件选择方式：
- **按编号**：`bash scripts/run.sh test 3` — 处理第 3 个文件
- **按文件名**：`bash scripts/run.sh test new.md` — 精确匹配
- **按关键词**：`bash scripts/run.sh test mmc3` — 模糊匹配文件名中包含 `mmc3` 的文件

## 🌐 Web 标注平台

### 架构概览

```
┌─────────────────────────────────────────────────────┐
│                    Vercel (前端)                      │
│  Next.js 15 App Router + TailwindCSS                │
│                                                     │
│  / ─────────────── 论文列表（SSR + ISR 60s）         │
│  /papers/[slug] ── 论文详情 + 基因卡片 + 标注        │
└────────────────────────┬────────────────────────────┘
                         │ Supabase JS Client
                         ▼
┌─────────────────────────────────────────────────────┐
│                  Supabase (后端)                      │
│                                                     │
│  papers ──── 论文 (MD原文 + JSON + 验证报告)         │
│  genes ───── 基因 (展平的字段数据 + AI验证结果)      │
│  annotations  专家标注 (逐字段 correct/incorrect)    │
│                                                     │
│  RLS 策略：匿名可读，认证用户可标注                   │
└─────────────────────────────────────────────────────┘
```

### 部署步骤

#### 1. 创建 Supabase 项目

1. 访问 [supabase.com](https://supabase.com) 创建免费项目
2. 进入 **SQL Editor**，粘贴并执行 `database/schema.sql`
3. 在 **Settings → API** 中获取 `Project URL` 和 `anon public key`

#### 2. 导入数据到 Supabase

```bash
# 安装 Python Supabase SDK
pip install supabase python-dotenv

# 在 .env 中添加（注意使用 service_role key，非 anon key）
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# 运行导入脚本
python scripts/import_to_supabase.py
```

#### 3. 配置 Web 前端

```bash
cd web

# 创建环境变量
cp .env.local.example .env.local

# 编辑 .env.local，填入 Supabase URL 和 anon key
# NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
# NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

#### 4. 本地开发

```bash
# 方式一：一键启动脚本（推荐，自动检测端口、等待就绪、打开浏览器）
bash scripts/dev.sh

# 指定端口
bash scripts/dev.sh --port 3001

# 强制 kill 占用端口的进程后启动
bash scripts/dev.sh --kill

# 方式二：手动启动
cd web
npm run dev
# 访问 http://localhost:3000
```

#### 5. 部署到 Vercel

```bash
# 方式一：通过 Vercel CLI
cd web
npx vercel

# 方式二：通过 GitHub
# 将项目推送到 GitHub，然后在 vercel.com 导入仓库
# Root Directory 设置为 "web"
```

在 Vercel Dashboard 中配置环境变量：
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### 页面说明

| 页面 | 路径 | 功能 |
|------|------|------|
| 论文列表 | `/` | 展示所有论文，显示标题、期刊、基因数、验证进度条 |
| 论文详情 | `/papers/{slug}` | 左栏 Markdown 原文 + 右栏基因卡片（含标注功能） |

### 标注操作

在论文详情页，每个基因字段旁有「标注」按钮，点击后可以：

1. **✅ 正确** — 确认 AI 提取结果正确
2. **❌ 错误** — 标记该字段提取有误
3. **✏️ 修改** — 提供修正值，替换错误的提取结果

每条标注可附加评论说明理由。
