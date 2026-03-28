# 🚀 run.sh 使用指南

`scripts/run.sh` 是整个 BioJSON Pipeline 的统一入口，负责设置环境变量并调用 Python 脚本。

---

## 一、基本用法

```bash
bash scripts/run.sh [模式] [参数]
```

---

## 二、所有模式一览

| 命令 | 作用 | 说明 |
|------|------|------|
| `bash scripts/run.sh` | 提取 + 验证（全量） | 默认模式，等同于 `all` |
| `bash scripts/run.sh all` | 提取 + 验证（全量） | 先 extract 再 verify |
| `bash scripts/run.sh extract` | 仅提取 | 只跑 `md_to_json.py`，MD → JSON |
| `bash scripts/run.sh verify` | 仅验证 | 只跑 `verify_response.py`，验证已有 JSON |
| `bash scripts/run.sh test` | 测试模式 | 只处理第 1 个文件（提取+验证） |
| `bash scripts/run.sh test 3` | 测试模式 | 只处理第 3 个文件 |
| `bash scripts/run.sh rerun` | 强制全部重跑 | 忽略已有结果，全部重新处理 |
| `bash scripts/run.sh rollback plcell` | 回退指定文件 | 删除对应 JSON/报告，MD 移回 `md/` |

---

## 三、增量处理（断点续跑）

默认情况下，脚本会**自动跳过已处理的文件**：

```bash
# 第 1 次运行：处理了 3 篇后断了
bash scripts/run.sh all

# 第 2 次运行：自动跳过已完成的 3 篇，继续处理剩余的
bash scripts/run.sh all
```

输出示例：
```
  ⏭️  已存在，跳过: reports/raw_extractions/论文1_nutri_plant.json
  ⏭️  已存在，跳过: reports/raw_extractions/论文2_nutri_plant.json
  ✅ 成功处理: 论文3.md -> reports/raw_extractions/论文3_nutri_plant.json
```

### 强制重跑（忽略已有结果）

```bash
# 方式 1：使用 rerun 模式
bash scripts/run.sh rerun

# 方式 2：设置环境变量（可以只重跑某个阶段）
FORCE_RERUN=1 bash scripts/run.sh extract    # 只重跑提取
FORCE_RERUN=1 bash scripts/run.sh verify     # 只重跑验证
```

---

## 四、自定义参数

### 4.1 更换模型

```bash
MODEL="gpt-4o" bash scripts/run.sh all
```

### 4.2 调整温度和 max_tokens

```bash
TEMPERATURE=0.3 MAX_TOKENS=16384 bash scripts/run.sh all
```

### 4.3 组合使用

```bash
MODEL="gpt-4o" TEMPERATURE=0.5 FORCE_RERUN=1 bash scripts/run.sh extract
```

---

## 五、环境变量完整列表

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `BASE_DIR` | `/data/haotianwu/biojson` | 项目根目录 |
| `MD_DIR` | `${BASE_DIR}/md` | 输入 Markdown 目录 |
| `JSON_DIR` | `${BASE_DIR}/json` | 最终验证后 JSON 目录 |
| `RAW_EXTRACTIONS_DIR` | `${BASE_DIR}/reports/raw_extractions` | 初始提取结果目录 |
| `VERIFICATIONS_DIR` | `${BASE_DIR}/reports/verifications` | 验证报告目录 |
| `EXTRACT_TOKENS_DIR` | `${BASE_DIR}/reports/extract_tokens` | 提取 token 消耗目录 |
| `VERIFY_TOKENS_DIR` | `${BASE_DIR}/reports/verify_tokens` | 验证 token 消耗目录 |
| `PROMPT_PATH` | `configs/nutri_plant.txt` | 提取用的 System Prompt |
| `SCHEMA_PATH` | `configs/nutri_plant.json` | 字段 Schema 定义 |
| `MODEL` | `Vendor2/Claude-4.6-opus` | 使用的模型 |
| `MAX_TOKENS` | `18192` | 最大输出 token |
| `TEMPERATURE` | `0.7` | 采样温度 |
| `FORCE_RERUN` | 未设置 | 设为 `1` 时强制重跑 |
| `TEST_MODE` | 未设置 | 设为 `1` 时进入测试模式 |
| `TEST_INDEX` | `1` | 测试模式下处理第几个文件 |

---

## 六、执行流程图

```
bash scripts/run.sh all
│
├── 1. 设置环境变量（路径、模型、参数）
│
├── 2. 运行 md_to_json.py（提取阶段）
│       ├── 遍历 md/ 中所有 .md 文件
│       ├── 每个文件：
│       │   ├── 检查 raw_extractions/ 中是否已有结果 → 有则跳过
│       │   ├── 读取 MD → strip_references 去除引用列表
│       │   ├── 调用 LLM API (function_calling)
│       │   └── 保存到 reports/raw_extractions/
│       └── 保存 token 报告到 reports/extract_tokens/
│
└── 3. 运行 verify_response.py（验证阶段）
        ├── 配对 md/ 和 raw_extractions/ 中的文件
        ├── 每个文件：
        │   ├── 检查 json/ 中是否已有 verified 结果 → 有则跳过
        │   ├── 逐基因调用 LLM 验证每个字段
        │   ├── UNSUPPORTED → 改为 "NA"
        │   ├── 保存 verified JSON 到 json/
        │   └── 保存验证报告到 reports/verifications/
        └── 保存 token 报告到 reports/verify_tokens/
```

---

## 七、常见场景

### 场景 1：第一次跑全部论文
```bash
bash scripts/run.sh all
```

### 场景 2：添加了新论文，只处理新的
```bash
# 把新论文的 .md 放到 md/ 目录，然后直接跑
bash scripts/run.sh all
# 旧论文自动跳过，只处理新的
```

### 场景 3：改了 Prompt，想重新提取但不重新验证
```bash
FORCE_RERUN=1 bash scripts/run.sh extract
bash scripts/run.sh verify   # 验证时也会因为 verified JSON 已存在而跳过
                              # 如果也想重新验证：
FORCE_RERUN=1 bash scripts/run.sh verify
```

### 场景 4：只想测试一篇论文看效果
```bash
bash scripts/run.sh test 2   # 只处理第 2 篇
```

### 场景 5：查看有哪些论文待处理
```bash
ls md/              # 待处理的输入
ls md/processed/    # 已处理完的 MD
ls json/            # 已验证的最终 JSON
```

### 场景 6：回退某篇论文（重新处理）
```bash
# 回退 = 删除对应的 JSON + 报告，把 MD 从 processed/ 移回 md/
bash scripts/run.sh rollback plcell                # 模糊匹配
bash scripts/run.sh rollback plcell_v31_5_937      # 不带 MinerU 前缀也行
bash scripts/run.sh rollback plcell.md             # 带 .md 后缀也行

# 回退后重新跑
bash scripts/run.sh test plcell
```
