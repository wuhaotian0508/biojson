---
name: biojson-extraction
description: >
  BioJSON 论文基因提取与验证流水线。当用户要求从论文 MD 中提取基因信息、验证提取结果、
  调试 schema/prompt、排查截断或字符串数组问题、或修改 pipeline 代码时，使用此技能。
  核心特点：每篇论文只需 2 次 API 调用（提取 + 验证），由 pipeline.py 协调。
version: 2.0.0
tags: [biojson, extraction, verification, llm, function-calling, pipeline]
---

# BioJSON 提取与验证流水线

## 项目架构

```
biojson/
├── configs/                     # LLM 配置
│   ├── nutri_gene_prompt_v2.txt # System Prompt（角色 + 步骤指令）
│   └── nutri_gene_schema_v2.json# 三类基因的字段定义（CommonGene / PathwayGene / RegulationGene）
├── scripts/
│   ├── pipeline.py              # ★ 流水线协调器（入口）
│   ├── md_to_json.py            # 提取模块：4 个 tools（classify + 3×extract）
│   ├── verify_response.py       # 验证模块：1 个 tool（verify_all_genes）
│   ├── text_utils.py            # MD 预处理（去图片/引用/致谢）
│   ├── token_tracker.py         # Token 用量追踪
│   ├── run.sh                   # Shell 入口（调用 pipeline.py）
│   └── rollback.py              # 回退工具
├── md/                          # 输入：论文 Markdown
│   └── processed/               # 已完成的 MD（验证后移入）
├── reports/{paper-dir}/         # 中间产物
│   ├── extraction.json          # 提取结果（三数组结构）
│   ├── gene_dict.json           # 基因分类字典（断点恢复用）
│   └── verification.json        # 验证报告
├── json/                        # 最终产物：verified JSON
└── skills/biojson-extraction/   # 本技能
    ├── SKILL.md                 # 本文件
    ├── check_extraction.py      # 批量检查提取质量
    └── fix_string_genes.py      # 修复字符串数组问题
```

## 核心数据流：每篇论文 2 次 API 调用

### 第一次 API 调用：提取（md_to_json.py）

读入 MD 论文一次，通过 parallel function calling 给 LLM 提供 4 个 tools：

| Tool | 功能 | 输出大小 |
|------|------|----------|
| `classify_genes` | 识别所有核心基因 + 分类（Common/Pathway/Regulation） | 很小（每基因 ~3 字段） |
| `extract_common_genes` | 提取 Common 基因的详细字段 | 中等 |
| `extract_pathway_genes` | 提取 Pathway 基因的详细字段 | 中等 |
| `extract_regulation_genes` | 提取 Regulation 基因的详细字段 | 中等 |

**LLM 行为**：先调 `classify_genes` 确定基因列表和分类，然后根据分类结果按需调用对应的 extract tool。
不是所有 extract tool 都会被调用——如果论文没有 Common 基因，LLM 就不会调 `extract_common_genes`。

**输出**：
1. `reports/{paper-dir}/extraction.json` — 完整提取结果（三数组结构）
2. `reports/{paper-dir}/gene_dict.json` — `{Gene_Name: category}` 映射（备份，供断点恢复）
3. `gene_dict` — 内存中的 Python dict，传递给验证阶段

### 第二次 API 调用：验证（verify_response.py）

读入 MD 论文第二次 + extraction.json，一次性验证所有基因的所有非 NA 字段：

| Tool | 功能 |
|------|------|
| `verify_all_genes` | 对每个基因的每个非 NA 字段给出 SUPPORTED/UNSUPPORTED/UNCERTAIN 判定 |

**LLM 行为**：一次性接收 MD 全文 + 所有基因字段，批量返回验证结果。

**输出**：
1. `json/{paper}_nutri_plant_verified.json` — 修正后的最终 JSON（UNSUPPORTED → "NA"）
2. `reports/{paper-dir}/verification.json` — 验证报告（每字段的判定和理由）
3. MD 文件移入 `md/processed/`

### 成本对比

| 架构 | API 调用次数 | MD Prompt 消耗 |
|------|-------------|---------------|
| 旧（md_to_json + verify×N基因） | 1 + N | (1+N) × MD长度 |
| **新（pipeline）** | **2** | **2 × MD长度** |

## configs 说明

### nutri_gene_schema_v2.json
定义三类基因的字段结构。包含 4 个顶层 key：
- `CommonGeneExtraction` — Common 基因字段（30 个）
- `PathwayGeneExtraction` — Pathway 基因字段（42 个，多了酶/底物/通路等）
- `RegulationGeneExtraction` — Regulation 基因字段（43 个，多了 TF/靶标/调控等）
- `MultipleGeneExtraction` — 合并版（旧架构用，新架构不再使用）

**修改 schema 后注意**：需要同步更新 `md_to_json.py` 中的 `_schema_props_to_fc()` 调用。

### nutri_gene_prompt_v2.txt
System Prompt，指导 LLM 的角色和行为。不需要频繁修改。

## 运行方式

```bash
# 推荐：新流水线（2 次 API/篇）
bash scripts/run.sh pipeline

# 测试模式
bash scripts/run.sh pipeline-test
bash scripts/run.sh pipeline-test 3
bash scripts/run.sh pipeline-test new

# 旧模式仍保留（兼容）
bash scripts/run.sh extract    # 仅提取
bash scripts/run.sh verify     # 仅验证
bash scripts/run.sh all        # 提取 + 验证（旧方式）
```

## 常见故障排查

### 1. JSON 截断（基因数据不完整）
**现象**：extraction.json 中某类基因数组被截断
**原因**：LLM 输出 token 超限
**解决**：新架构已将 tool 拆小，截断概率大幅降低。如仍截断，可调高 `max_tokens`

### 2. 字符串数组（基因是字符串而非对象）
**现象**：`check_extraction.py` 报告 "Common_Genes: 3/5 个基因是字符串而非对象"
**原因**：LLM 偶发把对象序列化为描述字符串
**解决**：
- 应急：`python skills/biojson-extraction/fix_string_genes.py --fix`
- 根治：rollback + 重新提取

### 3. 分类不准确
**现象**：一个明显的 pathway 酶被分到了 Common_Genes
**解决**：检查 `reports/{paper}/gene_dict.json` 的 reason 字段，必要时调整 prompt 中的分类标准描述

### 4. 验证过于严格 / 过于宽松
**调整**：修改 `verify_response.py` 中的 `VERIFY_SYSTEM_PROMPT`

## 代码修改注意事项

1. **改字段**：修改 `configs/nutri_gene_schema_v2.json` 中对应类别的 properties → `md_to_json.py` 会自动读取
2. **改 prompt**：修改 `configs/nutri_gene_prompt_v2.txt` → 立即生效
3. **改 tool 逻辑**：修改 `scripts/md_to_json.py` 中的 tool 定义和 handler
4. **改验证逻辑**：修改 `scripts/verify_response.py` 中的 `VERIFY_SYSTEM_PROMPT` 和 `VERIFY_ALL_TOOL`
5. **改流程编排**：修改 `scripts/pipeline.py`
