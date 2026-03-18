# BioJSON

基于 LLM 的植物营养代谢基因文献结构化提取管道（Pipeline）。

从科学文献（Markdown 格式）中自动提取关键基因信息为结构化 JSON，并通过 LLM 二次验证消除幻觉（Hallucination），确保提取结果忠实于原文。

## ✨ 功能特性

- **MD → JSON 结构化提取**：使用 LLM Function Calling 按预定义 JSON Schema，从文献中提取作物营养代谢关键基因的详细信息（基因名、物种、代谢通路、表型效应、实验方法等 40+ 字段）
- **幻觉验证与自动修正**：调用 LLM 逐基因、逐字段验证提取结果是否有原文支持，将不支持的字段（UNSUPPORTED）自动修正为 `"NA"`
- **文本预处理**：自动去除论文中的图片、URL、引用列表、致谢等无用内容，减少 Token 消耗
- **增量处理**：自动跳过已处理的文件，支持 `FORCE_RERUN=1` 强制重跑
- **Fallback 机制**：当主 API 因内容审查被拦截时，自动切换到备用 API
- **截断 JSON 自动修复**：当 LLM 输出被截断时，自动修复不完整的 JSON 结构
- **Token 用量追踪**：记录每次 API 调用的 Token 消耗（输入/输出/合计），生成 JSON 格式的用量报告

## 📁 项目结构

```
biojson/
├── configs/                    # 配置文件
│   ├── nutri_plant.txt         #   提取 Prompt（指导 LLM 如何阅读文献、识别核心基因）
│   └── nutri_plant.json        #   JSON Schema（定义输出结构和字段说明）
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
│   └── token_tracker.py        #   Token 用量追踪模块
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

### Prompt (`configs/nutri_plant.txt`)

指导 LLM 进行三步操作：
1. **代谢感知阅读**：深入阅读文献，定义营养性状目标，识别代谢通路和核心基因（严格限定为有直接实验干预的基因）
2. **结构化提取**：按 Schema 通过 Function Calling 提取核心基因的详细信息，遵循「最终营养产物必须关联」「通路步骤锚定」「方向性必须明确」等原则
3. **验证审核**：检查核心基因有效性、性状有效性、方向一致性和证据对齐

### JSON Schema (`configs/nutri_plant.json`)

定义了 `CropNutrientMetabolismGeneExtraction` 模板，包含：
- **论文级字段**：Title、Journal、DOI
- **基因级字段（40+ 个）**：涵盖基因基本信息、代谢角色、通路定位、表型效应、调控机制、实验证据、变异信息、育种价值等

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
