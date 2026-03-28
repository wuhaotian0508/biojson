# `run.sh` 逐行解析与使用指南

> 本文档详细解析 `scripts/run.sh` 的每一个部分，帮助理解 BioJSON Pipeline 的整体架构和运行流程。

---

## 📋 目录

1. [整体架构概览](#1-整体架构概览)
2. [Shebang 与脚本头部](#2-shebang-与脚本头部)
3. [基础路径配置](#3-基础路径配置)
4. [配置文件路径](#4-配置文件路径)
5. [模型参数](#5-模型参数)
6. [运行模式与参数解析](#6-运行模式与参数解析)
7. [启动信息打印](#7-启动信息打印)
8. [`case` 分支：核心调度逻辑](#8-case-分支核心调度逻辑)
9. [各模式使用示例](#9-各模式使用示例)
10. [环境变量传递机制详解](#10-环境变量传递机制详解)
11. [Pipeline 数据流图](#11-pipeline-数据流图)
12. [常见问题 FAQ](#12-常见问题-faq)

---

## 1. 整体架构概览

`run.sh` 是 BioJSON 项目的**统一入口脚本**，负责：

```
┌─────────────────────────────────────────────────────────┐
│                     run.sh 的职责                        │
├─────────────────────────────────────────────────────────┤
│  1. 定义所有路径（输入/输出/配置）                         │
│  2. 设置模型参数（model/temperature/max_tokens）          │
│  3. 解析用户传入的运行模式                                │
│  4. 调度执行对应的 Python 脚本                            │
└─────────────────────────────────────────────────────────┘
```

整个 Pipeline 分两步：

| 步骤 | 脚本 | 功能 |
|------|------|------|
| Step 1: 提取 | `md_to_json.py` | 读取 Markdown 论文 → 调用 LLM → 输出结构化 JSON |
| Step 2: 验证 | `verify_response.py` | 读取 JSON + 原文 → 调用 LLM 逐字段验证 → 修正幻觉 |

---

## 2. Shebang 与脚本头部

```bash
#!/bin/bash
```

- `#!/bin/bash`：指定用 **Bash** 解释器执行本脚本
- 后面的注释块是用法说明，不影响执行

**用法速查：**
```bash
bash scripts/run.sh              # 默认: 提取 + 验证（全量）
bash scripts/run.sh extract      # 仅提取 MD → JSON
bash scripts/run.sh verify       # 仅验证 JSON
bash scripts/run.sh all          # 提取 + 验证（全量）
bash scripts/run.sh test         # 测试模式: 仅处理第 1 个文件
bash scripts/run.sh test 3       # 测试模式: 仅处理第 3 个文件
```

---

## 3. 基础路径配置

```bash
export BASE_DIR="/data/haotianwu/biojson"
export MD_DIR="${BASE_DIR}/md"
export JSON_DIR="${BASE_DIR}/json"
export REPORT_DIR="${BASE_DIR}/reports"
```

### 逐行解析

| 变量 | 值 | 用途 |
|------|----|------|
| `BASE_DIR` | `/data/haotianwu/biojson` | 项目根目录 |
| `MD_DIR` | `.../md` | 存放待处理的 Markdown 论文 |
| `JSON_DIR` | `.../json` | 存放 LLM 生成的 JSON 结果 |
| `REPORT_DIR` | `.../reports` | 存放验证报告和 Token 用量报告 |

### 关键点：`export` 的作用

`export` 使变量成为**环境变量**，这样子进程（Python 脚本）可以通过 `os.getenv()` 读取到这些值。

```python
# md_to_json.py 中的对应代码：
BASE_DIR = os.getenv("BASE_DIR", "/data/haotianwu/biojson")
INPUT_DIR = os.getenv("MD_DIR", os.path.join(BASE_DIR, "md"))
```

如果不用 `export`，变量只在 shell 内部可见，Python 脚本读不到。

### 目录结构对应

```
biojson/
├── md/                          ← MD_DIR: 输入
│   ├── MinerU_markdown_PIIS00928...md
│   ├── MinerU_markdown_s41467...md
│   └── ... (共 7 个 .md 文件)
├── json/                        ← JSON_DIR: 输出
│   ├── ..._nutri_plant.json          (提取结果)
│   └── ..._nutri_plant_verified.json (验证修正后)
├── reports/                     ← REPORT_DIR: 报告
│   ├── ..._verification.json
│   └── token_usage_*.json
├── configs/                     ← 配置文件
└── scripts/                     ← 脚本
```

---

## 4. 配置文件路径

```bash
export PROMPT_PATH="${BASE_DIR}/configs/nutri_plant.txt"
export SCHEMA_PATH="${BASE_DIR}/configs/nutri_plant.json"
```

| 变量 | 指向的文件 | 内容说明 |
|------|-----------|---------|
| `PROMPT_PATH` | `configs/nutri_plant.txt` | **System Prompt**：告诉 LLM 它是植物分子生物学专家，如何从论文中提取关键基因信息 |
| `SCHEMA_PATH` | `configs/nutri_plant.json` | **JSON Schema**：定义输出格式，包含 40+ 个字段（基因名、物种、通路、代谢物等） |

### Prompt 的核心逻辑（简化版）

```
Step 1: 阅读论文 → 识别核心基因（有直接实验证据的）
Step 2: 按 Schema 结构化提取信息
Step 3: 自我验证（代谢因果审计）
```

### Schema 的结构

```json
{
  "CropNutrientMetabolismGeneExtraction": {
    "Title": "论文标题",
    "Journal": "期刊名",
    "DOI": "DOI",
    "Genes": [
      {
        "Gene_Name": "ZmPSY1",
        "Species": "Maize",
        "Final_Nutrient_Product": "β-carotene",
        "Pathway_Name": "Carotenoid biosynthesis",
        "Core_Validation_Method": "Overexpression",
        ... // 共 40+ 个字段
      }
    ]
  }
}
```

---

## 5. 模型参数

```bash
export MODEL="${MODEL:-Vendor2/Claude-4.6-opus}"
export MAX_TOKENS="${MAX_TOKENS:-18192}"
export TEMPERATURE="${TEMPERATURE:-0}"
```

### `${VAR:-default}` 语法详解

这是 Bash 的**默认值语法**，含义是：

> 如果变量 `VAR` **已经设置过**，就用它的值；否则用 `default`。

**示例：**

```bash
# 场景 1：直接运行 run.sh（使用默认值）
bash scripts/run.sh
# → MODEL = "Vendor2/Claude-4.6-opus"

# 场景 2：在命令行覆盖模型
MODEL="gpt-4o" bash scripts/run.sh
# → MODEL = "gpt-4o"

# 场景 3：先 export 再运行
export MODEL="gpt-4o"
bash scripts/run.sh
# → MODEL = "gpt-4o"
```

### 参数含义

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `MODEL` | `Vendor2/Claude-4.6-opus` | 使用的 LLM 模型名称 |
| `MAX_TOKENS` | `18192` | LLM 最大生成 Token 数（约 13k-14k 汉字） |
| `TEMPERATURE` | `0` | 温度=0 表示确定性输出，无随机性（适合信息提取） |

---

## 6. 运行模式与参数解析

```bash
MODE="${1:-all}"
TEST_INDEX="${2:-1}"
```

### `$1` 和 `$2`：位置参数

| 语法 | 含义 |
|------|------|
| `$1` | 脚本的第 1 个参数 |
| `$2` | 脚本的第 2 个参数 |
| `${1:-all}` | 如果没传第 1 个参数，默认为 `"all"` |
| `${2:-1}` | 如果没传第 2 个参数，默认为 `"1"` |

**对应关系举例：**

```bash
bash scripts/run.sh test 3
#                    ↑    ↑
#                    $1   $2
#                    MODE=test  TEST_INDEX=3
```

> ⚠️ 注意：`MODE` 和 `TEST_INDEX` 没有 `export`，因为它们只在 shell 内部用于 `case` 分支判断。但 `TEST_INDEX` 后续会在 `test` 模式中被 `export`。

---

## 7. 启动信息打印

```bash
echo "═══════════════════════════════════════════════════════"
echo "🚀 BioJSON Pipeline"
echo "   模式:     ${MODE}"
echo "   模型:     ${MODEL}"
echo "   输入目录: ${MD_DIR}"
echo "   输出目录: ${JSON_DIR}"
if [ "$MODE" = "test" ]; then
echo "   测试文件: 第 ${TEST_INDEX} 个"
fi
echo "═══════════════════════════════════════════════════════"
```

运行效果：

```
═══════════════════════════════════════════════════════════
🚀 BioJSON Pipeline
   模式:     test
   模型:     Vendor2/Claude-4.6-opus
   输入目录: /data/haotianwu/biojson/md
   输出目录: /data/haotianwu/biojson/json
   测试文件: 第 3 个
═══════════════════════════════════════════════════════════
```

### `if` 语句解析

```bash
if [ "$MODE" = "test" ]; then
    # 只有测试模式才打印文件编号
fi
```

- `[ ... ]`：Bash 的条件测试语法（等价于 `test` 命令）
- `"$MODE"` 加引号防止变量为空时语法错误
- `=`：字符串比较

---

## 8. `case` 分支：核心调度逻辑

```bash
case $MODE in
  extract)
    python scripts/md_to_json.py
    ;;
  verify)
    python scripts/verify_response.py
    ;;
  all)
    python scripts/md_to_json.py && python scripts/verify_response.py
    ;;
  test)
    export TEST_MODE=1
    export TEST_INDEX="${TEST_INDEX}"
    python scripts/md_to_json.py && python scripts/verify_response.py
    ;;
  *)
    echo "❌ 未知模式: ${MODE}"
    exit 1
    ;;
esac
```

### `case` 语法速查

```
case 变量 in
  模式1)
    命令...
    ;;          ← 相当于 break
  模式2)
    命令...
    ;;
  *)            ← 相当于 default（匹配所有其他情况）
    命令...
    ;;
esac            ← case 的反写，结束标志
```

### 各模式详解

#### `extract` — 仅提取

```bash
python scripts/md_to_json.py
```

执行流程：
```
md/*.md → LLM(prompt + schema) → json/*_nutri_plant.json
```

#### `verify` — 仅验证

```bash
python scripts/verify_response.py
```

执行流程：
```
md/*.md + json/*_nutri_plant.json → LLM(逐基因验证) → json/*_verified.json + reports/*_verification.json
```

#### `all` — 先提取再验证（默认模式）

```bash
python scripts/md_to_json.py && python scripts/verify_response.py
```

- `&&`：**短路与**运算符。只有前一条命令**成功**（返回码 0）时才执行后一条
- 如果提取失败，验证不会执行（避免验证空文件）

#### `test` — 测试模式

```bash
export TEST_MODE=1
export TEST_INDEX="${TEST_INDEX}"
python scripts/md_to_json.py && python scripts/verify_response.py
```

关键点：
- `export TEST_MODE=1`：告诉 Python 脚本进入测试模式
- `export TEST_INDEX`：告诉 Python 处理第几个文件

Python 端如何接收：

```python
# md_to_json.py 中：
if os.getenv("TEST_MODE") == "1":
    idx = int(os.getenv("TEST_INDEX", "1")) - 1  # 转为 0-based
    files = [files[idx]]  # 只保留第 idx 个文件
```

#### `*` — 错误处理

```bash
*)
    echo "❌ 未知模式: ${MODE}"
    exit 1
    ;;
```

- `exit 1`：以非零状态码退出，表示出错

---

## 9. 各模式使用示例

### 示例 1：首次使用，先测试一个文件

```bash
# 处理第 1 个 md 文件（提取 + 验证）
bash scripts/run.sh test

# 输出：
# 🧪 测试模式: 仅处理第 1 个文件 → MinerU_markdown_mmc3_2031567019886178304.md
# 成功处理: ... → json/..._nutri_plant.json
# 🧪 测试模式: 仅验证第 1 个文件
# ... 验证报告 ...
```

### 示例 2：测试第 3 个文件

```bash
bash scripts/run.sh test 3

# 文件按字母排序后，选择第 3 个：
# MinerU_markdown_PIIS009286741731499X_2031567088198815744.md
```

### 示例 3：只做提取，不做验证

```bash
bash scripts/run.sh extract
# 适用场景：想先看看提取结果，再决定是否验证
```

### 示例 4：已有 JSON，只做验证

```bash
bash scripts/run.sh verify
# 适用场景：提取已经完成，只想重新验证（比如换了验证 prompt 后）
```

### 示例 5：全量处理

```bash
bash scripts/run.sh all
# 或直接：
bash scripts/run.sh
# （默认就是 all 模式）
```

### 示例 6：切换模型

```bash
MODEL="gpt-4o" MAX_TOKENS=16384 bash scripts/run.sh test
# 用 gpt-4o 模型，最大输出 16384 tokens，测试第 1 个文件
```

### 示例 7：后台运行全量处理

```bash
nohup bash scripts/run.sh all > pipeline.log 2>&1 &
# nohup: 退出终端后继续运行
# > pipeline.log: 输出重定向到日志文件
# 2>&1: 错误输出也写入日志
# &: 后台运行
```

---

## 10. 环境变量传递机制详解

`run.sh` 的一个核心设计是**用环境变量统一管理配置**，避免每个 Python 脚本各写各的路径。

### 传递链路

```
run.sh (export 环境变量)
  │
  ├──→ md_to_json.py     os.getenv("MD_DIR")
  │      └──→ token_tracker.py
  │
  └──→ verify_response.py  os.getenv("JSON_DIR")
         └──→ token_tracker.py
```

### 完整变量表

| 环境变量 | 设置位置 | 读取位置 | 说明 |
|----------|---------|---------|------|
| `BASE_DIR` | run.sh | md_to_json.py, verify_response.py | 项目根 |
| `MD_DIR` | run.sh | 两个 Python 脚本 | MD 输入目录 |
| `JSON_DIR` | run.sh | 两个 Python 脚本 | JSON 输出目录 |
| `REPORT_DIR` | run.sh | 两个 Python 脚本 | 报告目录 |
| `PROMPT_PATH` | run.sh | md_to_json.py | Prompt 文件路径 |
| `SCHEMA_PATH` | run.sh | md_to_json.py | Schema 文件路径 |
| `MODEL` | run.sh | 两个 Python 脚本 | 模型名 |
| `MAX_TOKENS` | run.sh | 两个 Python 脚本 | 最大生成 Token |
| `TEMPERATURE` | run.sh | 两个 Python 脚本 | 温度参数 |
| `TEST_MODE` | run.sh (test 模式) | 两个 Python 脚本 | 是否测试模式 |
| `TEST_INDEX` | run.sh (test 模式) | 两个 Python 脚本 | 测试文件编号 |
| `OPENAI_API_KEY` | `.env` 文件 | 两个 Python 脚本 | API 密钥 |
| `OPENAI_BASE_URL` | `.env` 文件 | 两个 Python 脚本 | API 地址 |

---

## 11. Pipeline 数据流图

```
                        ┌─────────────────┐
                        │   configs/      │
                        │  nutri_plant.txt│ ← System Prompt
                        │  nutri_plant.json│← JSON Schema
                        └────────┬────────┘
                                 │
 ┌──────────┐    Step 1: extract │    ┌──────────────────────┐
 │  md/     │ ──────────────────────→ │  json/               │
 │ *.md     │    md_to_json.py   │    │ *_nutri_plant.json   │
 │ (论文)   │                    │    │ (LLM 提取结果)        │
 └──────────┘                    │    └──────────┬───────────┘
      │                          │               │
      │     Step 2: verify       │               │
      └──────────────────────────────────────────┤
           verify_response.py    │               │
                                 │               ▼
                        ┌────────┴───────────────────────┐
                        │  json/*_verified.json          │
                        │  (修正幻觉后的 JSON)             │
                        ├────────────────────────────────┤
                        │  reports/*_verification.json   │
                        │  (验证报告: 每个字段的判定)       │
                        ├────────────────────────────────┤
                        │  reports/token_usage_*.json    │
                        │  (Token 用量统计)               │
                        └────────────────────────────────┘
```

---

## 12. 常见问题 FAQ

### Q1: 为什么用 `&&` 而不是 `;` 连接两条命令？

```bash
# && : 前一条成功才执行后一条
python scripts/md_to_json.py && python scripts/verify_response.py

# ;  : 不管前一条是否成功都执行后一条
python scripts/md_to_json.py ; python scripts/verify_response.py
```

如果提取失败了（比如 API 报错），JSON 文件不完整，此时再验证没有意义。用 `&&` 可以避免这种情况。

### Q2: `export` 和直接赋值有什么区别？

```bash
# 仅当前 shell 可见（子进程看不到）
MY_VAR="hello"

# 当前 shell + 所有子进程都可见
export MY_VAR="hello"
```

因为 `python scripts/xxx.py` 是以**子进程**方式运行的，所以必须 `export`。

### Q3: 如何只看提取结果而不调 API 验证？

```bash
bash scripts/run.sh extract
# 然后手动检查 json/ 目录下的文件
cat json/*_nutri_plant.json | python -m json.tool
```

### Q4: 文件编号是怎么确定的？

Python 脚本按文件名**字母排序**后，用 1-based 编号：

```
#1  MinerU_markdown_mmc10_2031567061837611008.md
#2  MinerU_markdown_mmc3_2031567019886178304.md
#3  MinerU_markdown_PIIS009286741731499X_2031567088198815744.md
#4  MinerU_markdown_plcell_v31_5_937_2031566954798968832.md
#5  MinerU_markdown_s41467-024-51114-1_2031567126488616960.md
#6  MinerU_markdown_s41586-022-04950-4_(1)_2031567254796566528.md
#7  MinerU_markdown_tieman2017_2031567451551371264.md
```

> ⚠️ 注意：字母排序中 `mmc10` 排在 `mmc3` 前面（因为 `1` < `3`），这是字典序而非数值序。

### Q5: `.env` 文件放在哪里？

`md_to_json.py` 和 `verify_response.py` 都使用了 `load_dotenv()`，会自动从项目根目录的 `.env` 文件加载：

```env
# .env 文件示例
OPENAI_API_KEY=sk-xxxxxxxxxxxx
OPENAI_BASE_URL=https://your-api-endpoint/v1
```

---

## 🧠 总结

`run.sh` 的设计理念：

1. **单一入口**：一个脚本管理所有配置和运行模式
2. **环境变量驱动**：通过 `export` 将配置传递给 Python 子进程
3. **灵活覆盖**：`${VAR:-default}` 语法允许命令行临时覆盖参数
4. **渐进式使用**：`test` 模式方便调试单个文件，`all` 模式全量处理
5. **流水线安全**：`&&` 确保前一步成功才执行下一步
