# 断点续运行（增量模式）原理说明

> 相关文件：`scripts/run.sh`、`scripts/md_to_json.py`、`scripts/verify_response.py`

## 概述

BioJSON Pipeline **默认以增量模式运行**：每次执行时，自动跳过已成功处理的文件，只处理尚未完成的文件。这意味着如果运行中途中断（API 报错、网络断开、手动终止等），再次运行 `bash scripts/run.sh` 即可**从断点处继续**，无需重头开始。

---

## 1. 核心原理

增量模式的判断逻辑非常简单：**检查输出文件是否已存在**。

Pipeline 分为两个阶段，每个阶段都独立实现了这一检查：

### 1.1 提取阶段（`md_to_json.py`）

在 `ai_response()` 函数开头：

```python
output_path = os.path.join(OUTPUT_DIR, f'{filename}_nutri_plant.json')
if os.path.exists(output_path) and os.getenv("FORCE_RERUN") != "1":
    print(f"  ⏭️  已存在，跳过: {output_path}")
    return
```

**判断依据**：`reports/raw_extractions/{filename}_nutri_plant.json` 是否存在。

- 存在 → 说明该文件已成功提取过，直接 `return` 跳过
- 不存在 → 说明该文件尚未处理（或上次处理到一半失败了，没来得及写出文件），调用 API 进行提取

### 1.2 验证阶段（`verify_response.py`）

在 `verify_file()` 函数开头：

```python
verified_json_path = os.path.join(FINAL_JSON_DIR, f"{stem}_nutri_plant_verified.json")
if os.path.exists(verified_json_path) and os.getenv("FORCE_RERUN") != "1":
    print(f"  ⏭️  已验证，跳过: {stem}")
    return None
```

**判断依据**：`json/{stem}_nutri_plant_verified.json` 是否存在。

- 存在 → 跳过
- 不存在 → 调用 API 进行验证

---

## 2. 工作流程图

```
bash scripts/run.sh
  │
  ├─ 提取阶段: md_to_json.py 遍历 md/ 下所有 .md 文件
  │    ├─ 文件A.md → raw_extractions/文件A_nutri_plant.json 已存在? → ⏭️ 跳过
  │    ├─ 文件B.md → raw_extractions/文件B_nutri_plant.json 已存在? → ⏭️ 跳过
  │    └─ 文件C.md → raw_extractions/文件C_nutri_plant.json 不存在  → 🚀 调用 API 提取
  │
  └─ 验证阶段: verify_response.py 遍历所有 md + json 文件对
       ├─ 文件A → json/文件A_nutri_plant_verified.json 已存在? → ⏭️ 跳过
       ├─ 文件B → json/文件B_nutri_plant_verified.json 不存在  → 🚀 调用 API 验证
       └─ 文件C → json/文件C_nutri_plant_verified.json 不存在  → 🚀 调用 API 验证
```

---

## 3. 为什么这样设计能实现"断点续运行"？

关键在于**输出文件只在处理成功后才写入**：

1. `md_to_json.py` 中，API 调用成功 + JSON 解析成功后，才执行 `f.write(final_output)` 写入输出文件
2. `verify_response.py` 中，所有基因验证完成 + 修正后，才执行 `json.dump()` 写入 verified JSON

因此：

- 如果某个文件**处理到一半就中断**了（比如 API 超时），输出文件**不会被写入**
- 下次运行时，`os.path.exists()` 检查发现输出不存在，就会**重新处理该文件**
- 而之前已经**成功处理**的文件，输出已写入，会被自动跳过

---

## 4. 运行终端输出示例

增量模式下，终端会显示哪些文件被跳过：

```
找到 7 个待处理文件...
  ⏭️  已存在，跳过: reports/raw_extractions/文件A_nutri_plant.json
  ⏭️  已存在，跳过: reports/raw_extractions/文件B_nutri_plant.json
  📏 文本预处理: 45,230 → 38,100 字符 (去除 References 列表节省 7,130 字符)
  ✅ Function calling 成功提取
  ✅ 成功处理: 文件C.md -> reports/raw_extractions/文件C_nutri_plant.json
```

---

## 5. 控制方式

### 5.1 默认行为（增量模式）

```bash
bash scripts/run.sh           # 跳过已有结果，从断点继续
bash scripts/run.sh extract   # 仅提取，增量
bash scripts/run.sh verify    # 仅验证，增量
bash scripts/run.sh all       # 提取+验证，增量
```

启动时会显示当前模式：

```
📋 增量模式: 跳过已处理的文件
```

### 5.2 强制重跑（忽略已有结果）

```bash
bash scripts/run.sh rerun                    # 提取+验证全部重跑
FORCE_RERUN=1 bash scripts/run.sh extract    # 仅强制重跑提取
FORCE_RERUN=1 bash scripts/run.sh verify     # 仅强制重跑验证
```

启动时会显示：

```
⚡ 强制重跑: 忽略已有结果
```

**原理**：当环境变量 `FORCE_RERUN=1` 时，`os.getenv("FORCE_RERUN") != "1"` 为 `False`，跳过逻辑的 `if` 条件不成立，所有文件都会被重新处理。

### 5.3 `run.sh` 中的相关代码

```bash
case $MODE in
  rerun)
    export FORCE_RERUN=1    # 设置环境变量，传递给 Python 脚本
    python scripts/md_to_json.py && python scripts/verify_response.py
    ;;
esac
```

---

## 6. 相关目录结构

| 目录 | 内容 | 作为断点判据 |
|------|------|-------------|
| `md/` | 输入的 Markdown 论文 | — |
| `md/processed/` | 已完成全流程的 MD 文件 | — |
| `reports/raw_extractions/` | 提取阶段的输出 JSON | ✅ 提取阶段检查此目录 |
| `json/` | 验证修正后的最终 JSON | ✅ 验证阶段检查此目录 |
| `reports/verifications/` | 验证报告（非判据） | — |

### 已处理文件自动归档

验证阶段成功完成后（verified JSON + 验证报告都已保存），MD 源文件会被**自动移动**到 `md/processed/` 目录：

```python
# verify_response.py - verify_file() 函数末尾
if os.path.exists(md_path):
    md_filename = os.path.basename(md_path)
    dest = os.path.join(PROCESSED_DIR, md_filename)
    shutil.move(md_path, dest)
    print(f"  📦 MD 已移动到: {dest}")
```

这样 `md/` 目录下只保留**尚未处理的文件**，一目了然。

---

## 7. 注意事项

1. **不要手动创建空的输出文件**，否则增量模式会误判为"已处理"而跳过。
2. 如果某个文件的输出**内容有问题**，需要重新处理，有两种方式：
   - 手动删除该文件的输出，然后重新运行 `bash scripts/run.sh`
   - 使用 `FORCE_RERUN=1` 强制全部重跑
3. 验证阶段内部**没有**基因级别的断点。如果一个文件有 10 个基因，验证到第 5 个时中断，下次会从该文件的第 1 个基因重新开始验证（因为 verified JSON 没写入）。断点粒度是**文件级**，不是基因级。
