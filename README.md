# BioJSON

基于 LLM 的植物营养代谢基因文献结构化提取管道（Pipeline）。

从科学文献（Markdown 格式）中自动提取关键基因信息为结构化 JSON，并通过 LLM 二次验证消除幻觉（Hallucination），确保提取结果忠实于原文。

## ✨ 功能特性

- **MD → JSON 结构化提取**：使用 LLM 按预定义 JSON Schema，从文献中提取作物营养代谢关键基因的详细信息（基因名、物种、代谢通路、表型效应、实验方法等 40+ 字段）
- **幻觉验证与自动修正**：调用 LLM 逐基因、逐字段验证提取结果是否有原文支持，将不支持的字段（UNSUPPORTED）自动修正为 `"NA"`
- **Token 用量追踪**：记录每次 API 调用的 Token 消耗（输入/输出/合计），生成 JSON 格式的用量报告

## 📁 项目结构

```
biojson/
├── configs/                    # 配置文件
│   ├── nutri_plant.txt         #   提取 Prompt（指导 LLM 如何阅读文献、识别核心基因）
│   └── nutri_plant.json        #   JSON Schema（定义输出结构和字段说明）
├── md/                         # 输入：Markdown 格式的科学文献
├── json/                       # 输出：提取的 JSON 和验证修正后的 JSON
├── reports/                    # 验证报告和 Token 用量报告
├── scripts/                    # 核心脚本
│   ├── run.sh                  #   统一运行入口（配置管理 + 模式选择）
│   ├── md_to_json.py           #   Step 1: MD → JSON 结构化提取
│   ├── verify_response.py      #   Step 2: JSON 幻觉验证与修正
│   └── token_tracker.py        #   Token 用量追踪模块
├── .env                        # 环境变量（API Key 等，不提交到 Git）
└── .gitignore
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install openai python-dotenv
```

### 2. 配置 API Key

在项目根目录创建 `.env` 文件：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://your-api-base-url/v1
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

# 测试模式：仅处理第 1 个文件
bash scripts/run.sh test

# 测试模式：仅处理第 3 个文件
bash scripts/run.sh test 3
```

## 📖 工作流程

```
科学文献 (MD)
      │
      ▼
┌─────────────┐     Prompt + Schema      ┌─────────────┐
│ md_to_json.py│ ──── LLM API ──────────▶ │  提取 JSON   │
└─────────────┘                          └──────┬──────┘
                                                │
                                                ▼
                                    ┌───────────────────┐
                                    │ verify_response.py │
                                    │  逐基因逐字段验证   │
                                    │  LLM 二次审查       │
                                    └────────┬──────────┘
                                             │
                                    ┌────────▼──────────┐
                                    │ 修正后的 JSON       │
                                    │ + 验证报告          │
                                    │ + Token 用量报告    │
                                    └───────────────────┘
```

## ⚙️ 配置说明

### Prompt (`configs/nutri_plant.txt`)

指导 LLM 进行三步操作：
1. **代谢感知阅读**：深入阅读文献，识别最终营养产物、代谢通路和核心基因
2. **结构化提取**：按 Schema 提取核心基因的详细信息
3. **验证审核**：检查提取结果的因果链和证据一致性

### JSON Schema (`configs/nutri_plant.json`)

定义了 `CropNutrientMetabolismGeneExtraction` 模板，包含：
- **论文级字段**：Title、Journal、DOI
- **基因级字段（40+ 个）**：涵盖基因基本信息、代谢角色、通路定位、表型效应、调控机制、实验证据、变异信息、育种价值等

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MODEL` | `Vendor2/Claude-4.6-opus` | LLM 模型名称 |
| `MAX_TOKENS` | `18192` | 最大输出 Token 数 |
| `TEMPERATURE` | `0` | 生成温度（0 = 确定性输出） |
| `TEST_MODE` | - | 设为 `1` 启用测试模式 |
| `TEST_INDEX` | `1` | 测试模式下处理的文件编号 |

## 📊 输出说明

- `json/{文献名}_nutri_plant.json` — 初始提取结果
- `json/{文献名}_nutri_plant_verified.json` — 验证修正后的结果
- `reports/{文献名}_verification.json` — 逐字段验证报告（SUPPORTED/UNSUPPORTED/UNCERTAIN）
- `reports/token_usage_*.json` — API Token 用量报告
