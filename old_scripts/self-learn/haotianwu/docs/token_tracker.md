# TokenTracker 变量与接口说明

> 源文件：`scripts/token_tracker.py`

## 概述

`TokenTracker` 用于追踪 API Token 用量，支持多次调用累计统计，并以 **kTokens**（千 token）为单位汇总。支持按阶段（如 `extract`、`verify`）分类统计，最终可打印摘要或保存为 JSON 报告。

---

## 1. `TokenTracker` 类

### 1.1 实例属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `model` | `str` | 使用的模型名称，如 `"Vendor2/Claude-4.6-opus"`，默认 `"unknown"`。用于报告中标识所用模型。 |
| `calls` | `list[dict]` | 存储每次 API 调用的详细记录列表。每条记录是一个字典（结构见下方 **调用记录字段**）。 |

### 1.2 调用记录字段（`calls` 列表中每个 `dict` 的键）

| 字段 | 类型 | 说明 |
|------|------|------|
| `stage` | `str` | 阶段标识。标记本次调用属于哪个流程阶段，如 `"extract"`（信息提取）或 `"verify"`（结果验证）。 |
| `file` | `str` | 本次调用处理的源文件名（通常为 Markdown 文件名）。 |
| `gene` | `str`（可选） | 验证的基因名。仅在 `verify` 阶段使用，`extract` 阶段不包含此字段。 |
| `prompt_tokens` | `int` | 本次调用的 **输入 token 数**（即 prompt / 请求部分消耗的 token）。 |
| `completion_tokens` | `int` | 本次调用的 **输出 token 数**（即模型生成的响应部分消耗的 token）。 |
| `total_tokens` | `int` | 本次调用的 **总 token 数**，等于 `prompt_tokens + completion_tokens`。 |
| `timestamp` | `str` | 调用发生的时间戳，ISO 8601 格式（如 `"2026-03-14T15:08:07.123456"`）。 |

### 1.3 `calls` 实际示例

**Extract 阶段**（无 `gene` 字段）：

```json
[
  {
    "stage": "extract",
    "file": "MinerU_markdown_mmc3_2031567019886178304.md",
    "prompt_tokens": 38030,
    "completion_tokens": 6451,
    "total_tokens": 44481,
    "timestamp": "2026-03-14T15:08:07.260192"
  }
]
```

**Verify 阶段**（包含 `gene` 字段，每个基因一次调用）：

```json
[
  {
    "stage": "verify",
    "file": "OsMYB110",
    "prompt_tokens": 40689,
    "completion_tokens": 3288,
    "total_tokens": 43977,
    "timestamp": "2026-03-14T17:05:18.118930",
    "gene": "OsMYB110"
  },
  {
    "stage": "verify",
    "file": "OsMYB55",
    "prompt_tokens": 40697,
    "completion_tokens": 3136,
    "total_tokens": 43833,
    "timestamp": "2026-03-14T17:06:07.942145",
    "gene": "OsMYB55"
  },
  {
    "stage": "verify",
    "file": "OsDREB2A",
    "prompt_tokens": 41137,
    "completion_tokens": 3092,
    "total_tokens": 44229,
    "timestamp": "2026-03-14T17:06:57.339472",
    "gene": "OsDREB2A"
  }
]
```

---

## 2. 实例方法

### `add(response, stage, file, gene)`

从 OpenAI 兼容的 API `response` 对象中提取 `usage` 信息，构建一条调用记录并追加到 `self.calls`。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `response` | API Response | — | OpenAI 格式的 API 返回对象，需包含 `.usage` 属性。 |
| `stage` | `str` | `"unknown"` | 阶段标识，如 `"extract"` 或 `"verify"`。 |
| `file` | `str` | `""` | 处理的文件名。 |
| `gene` | `str` | `""` | 基因名（仅 verify 阶段需要）。为空时不写入记录。 |

---

### `_aggregate(stage_filter)`

**内部方法**。按阶段聚合所有调用记录，返回汇总字典。

| 参数 | 说明 |
|------|------|
| `stage_filter` | `str` 或 `None`。若为 `None` 则统计所有调用；否则只统计指定阶段的调用。 |

`_aggregate` 不会被外部直接调用，它由 `get_summary()` 在内部驱动：

```python
# get_summary() 的核心逻辑：
stages = sorted(set(c["stage"] for c in self.calls))  # 找出所有出现过的阶段名，如 ["extract", "verify"]

for stage in stages:
    summary[stage] = self._aggregate(stage)   # 传入具体阶段名 → 只统计该阶段的 calls
summary["total"] = self._aggregate()          # 不传参（None） → 统计全部 calls
```

即：`stage_filter` 永远由 `get_summary()` 决定，不需要手动传入。

返回值字典的字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `prompt_tokens` | `int` | 输入 token 总数 |
| `completion_tokens` | `int` | 输出 token 总数 |
| `total_tokens` | `int` | 总 token 数 |
| `prompt_ktokens` | `float` | 输入 token 数 ÷ 1000，保留两位小数 |
| `completion_ktokens` | `float` | 输出 token 数 ÷ 1000，保留两位小数 |
| `total_ktokens` | `float` | 总 token 数 ÷ 1000，保留两位小数 |
| `calls` | `int` | 该阶段（或全部）的 API 调用次数 |

---

### `get_summary()`

获取完整的汇总数据。返回一个字典，键为各阶段名称（如 `"extract"`、`"verify"`）加上 `"total"`，值为各阶段对应的 `_aggregate()` 结果。

---

### `print_summary()`

在终端打印格式化的 Token 用量汇总表格，包括：
- 每个阶段的输入 / 输出 / 合计（kTokens）及调用次数
- 所有阶段的总计

---

### `save_report(path)`

将详细用量报告保存为 JSON 文件。

| 参数 | 说明 |
|------|------|
| `path` | 保存路径，如 `"reports/extract_tokens/token_usage_xxx.json"` |

JSON 报告结构：

```json
{
  "timestamp": "报告生成时间",
  "model": "模型名称",
  "calls": [ /* 每次调用的详细记录 */ ],
  "summary": { /* get_summary() 的结果 */ }
}
```

---

### `merge(other)`

将另一个 `TokenTracker` 实例的所有调用记录合并到当前实例中。用于汇总多个 tracker 的数据。

| 参数 | 说明 |
|------|------|
| `other` | 另一个 `TokenTracker` 实例 |

---

## 3. 模块级全局函数

用于在多个模块间共享同一个 `TokenTracker` 实例（单例模式）。

| 函数 | 说明 |
|------|------|
| `get_tracker(model)` | 获取全局 `TokenTracker` 单例。首次调用时创建，后续调用返回同一实例。 |
| `reset_tracker()` | 重置全局单例为 `None`，下次 `get_tracker()` 会创建新实例。 |

### 模块级变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `_global_tracker` | `TokenTracker \| None` | 全局单例的内部存储变量，由 `get_tracker()` 和 `reset_tracker()` 管理，不应直接访问。 |

---

## 4. 典型用法

```python
from token_tracker import TokenTracker

# 创建 tracker
tracker = TokenTracker(model="Vendor2/Claude-4.6-opus")

# 每次 API 调用后记录
response = client.chat.completions.create(...)
tracker.add(response, stage="extract", file="xxx.md")

# 验证阶段
response2 = client.chat.completions.create(...)
tracker.add(response2, stage="verify", file="xxx.md", gene="GeneA")

# 打印汇总
tracker.print_summary()

# 保存报告
tracker.save_report("reports/token_usage_xxx.json")
```
