---
name: biojson-extraction
description: >
  BioJSON 论文基因提取与验证流水线。从论文 MD 中提取基因信息、分类、验证。
  核心特点：SKILL.md 定义所有 tools，代码硬编码 3 次 API 调用顺序。
version: 4.0.0
tags: [biojson, extraction, verification, llm, function-calling, skill-driven]

tools:
  # ── 提取阶段：4 个 tools ──
  - name: classify_genes
    handler: handlers.handle_classify
    description: >
      Identify ALL core genes from the paper's Results section and classify each into one of three categories:
      - Common: genes that are neither pathway enzymes nor regulators (e.g., general functional genes)
      - Pathway: genes encoding enzymes in biosynthetic/metabolic pathways (e.g., CHS, F3H, PSY, DAHPS)
      - Regulation: genes encoding transcription factors, signaling proteins, or other regulators (e.g., MYB12, Del, Ros1, SPL)
      Only include genes that are directly experimentally validated in the Results section.
    parameters:
      type: object
      properties:
        Title:
          type: string
          description: "Full paper title."
        Journal:
          type: string
          description: "Journal name."
        DOI:
          type: string
          description: "Pure DOI string, no URL prefix."
        genes:
          type: array
          description: "List of all core genes identified from the paper."
          items:
            type: object
            properties:
              Gene_Name:
                type: string
                description: "Gene name or symbol."
              category:
                type: string
                enum: ["Common", "Pathway", "Regulation"]
                description: "Gene category."
              reason:
                type: string
                description: "Brief reason for classification."
            required: ["Gene_Name", "category"]
      required: ["Title", "Journal", "DOI", "genes"]

  - name: extract_common_genes
    handler: handlers.handle_extract_common
    description: >
      Extract detailed field information for Common genes (genes that are neither pathway enzymes nor regulators).
      Only call this tool if classify_genes identified Common genes. If information is not found, use 'NA'.
    schema_ref: "configs/nutri_gene_schema_v2.json#CommonGeneExtraction"

  - name: extract_pathway_genes
    handler: handlers.handle_extract_pathway
    description: >
      Extract detailed field information for Pathway genes (genes encoding enzymes in biosynthetic/metabolic pathways).
      Only call this tool if classify_genes identified Pathway genes. If information is not found, use 'NA'.
    schema_ref: "configs/nutri_gene_schema_v2.json#PathwayGeneExtraction"

  - name: extract_regulation_genes
    handler: handlers.handle_extract_regulation
    description: >
      Extract detailed field information for Regulation genes (transcription factors, signaling proteins, regulators).
      Only call this tool if classify_genes identified Regulation genes. If information is not found, use 'NA'.
    schema_ref: "configs/nutri_gene_schema_v2.json#RegulationGeneExtraction"

  # ── 验证阶段：1 个 tool ──
  - name: verify_all_genes
    handler: handlers.handle_verify_all
    description: >
      Submit verification results for ALL genes at once.
      For each gene, provide verdicts for each non-NA field.
    parameters:
      type: object
      properties:
        gene_verdicts:
          type: array
          description: "Verification results grouped by gene."
          items:
            type: object
            properties:
              Gene_Name:
                type: string
                description: "The gene name being verified."
              field_verdicts:
                type: array
                description: "Verification results for each field of this gene."
                items:
                  type: object
                  properties:
                    field_name:
                      type: string
                      description: "The field name being verified."
                    verdict:
                      type: string
                      enum: ["SUPPORTED", "UNSUPPORTED", "UNCERTAIN"]
                      description: "Verification verdict."
                    reason:
                      type: string
                      description: "Brief explanation for the verdict."
                  required: ["field_name", "verdict", "reason"]
            required: ["Gene_Name", "field_verdicts"]
      required: ["gene_verdicts"]
---

# BioJSON 提取与验证流水线

## 架构概述：硬编码 3 次 API 调用

本技能采用 **代码硬编码** 控制 API 调用顺序，不依赖 LLM 自由选择 tool。

### 核心方法

| 方法 | 用途 |
|------|------|
| `registry.call_tool(tool_name)` | 强制调用指定的单个 tool（`tool_choice` 锁定） |
| `registry.call_tools([tool1, tool2])` | 提供多个 tool，让 LLM 并行调用 |

### 3 次 API 调用流程

```
SKILL.md (YAML: tool 定义)
    ↓ load_skill()
ToolRegistry (注册 tools + handlers)
    ↓ 代码硬编码控制

API Call #1: call_tool("classify_genes")
    ↓ handle_classify() → gene_dict 存入 state
    ↓ 代码读取 gene_dict，决定需要哪些 extract tools

API Call #2: call_tools(["extract_pathway_genes", "extract_regulation_genes"])
    ↓ handle_extract_*() → extraction 存入 state
    ↓ 代码保存 extraction.json + gene_dict.json

API Call #3: call_tool("verify_all_genes")
    ↓ handle_verify_all() → verify_results 存入 state
    ↓ 代码应用修正，保存 verified JSON
```

### 与旧架构（run_loop）的区别

| 维度 | 旧架构 (run_loop) | 新架构 (call_tool) |
|------|-------------------|-------------------|
| 控制权 | LLM 自由选择 tool | **代码硬编码**每步调哪个 tool |
| API 次数 | 不确定（1~5 轮） | **固定 3 次** |
| 可靠性 | LLM 可能跳过 extract | **不可能跳过**，代码强制调用 |
| 调试 | 难以预测 LLM 行为 | 每步都有明确的输入输出 |

## 项目结构

```
biojson/
├── configs/
│   ├── nutri_gene_prompt_v2.txt     # System Prompt
│   └── nutri_gene_schema_v2.json    # 三类基因的字段定义（schema_ref 引用）
├── scripts/
│   ├── tool_registry.py             # ★ ToolRegistry 类 + call_tool/call_tools
│   ├── pipeline.py                  # 流水线协调器
│   ├── md_to_json.py                # 提取：API #1 classify + API #2 extract
│   ├── verify_response.py           # 验证：API #3 verify
│   ├── text_utils.py                # MD 预处理
│   ├── token_tracker.py             # Token 用量追踪
│   └── run.sh                       # Shell 入口
├── skills/biojson-extraction/       # ★ 本技能
│   ├── SKILL.md                     # 本文件（tool 定义 + 操作手册）
│   ├── handlers.py                  # tool handler 实现
│   ├── check_extraction.py          # 批量检查提取质量
│   └── fix_string_genes.py          # 修复字符串数组问题
├── md/                              # 输入：论文 Markdown
├── reports/{paper-dir}/             # 中间产物
│   ├── extraction.json              # 提取结果
│   ├── gene_dict.json               # 基因分类字典
│   └── verification.json            # 验证报告
└── json/                            # 最终产物：verified JSON
```

## 数据流

### API Call #1: classify_genes（md_to_json.py）

**代码**: `registry.call_tool("classify_genes")` — 强制调用

| 输入 | 输出 |
|------|------|
| MD 论文全文 + system prompt | gene_dict: `{Gene_Name: category}` |

handler `handle_classify()` 解析 LLM 返回，存入 `state["gene_dict"]`。

### API Call #2: extract_*_genes（md_to_json.py）

**代码**: `registry.call_tools(needed_tools)` — 根据 gene_dict 决定调哪些

| 条件 | 调用的 tool |
|------|------------|
| gene_dict 有 Pathway 类 | `extract_pathway_genes` |
| gene_dict 有 Regulation 类 | `extract_regulation_genes` |
| gene_dict 有 Common 类 | `extract_common_genes` |

handler `handle_extract_*()` 解析 LLM 返回，存入 `state["extraction"]`。

### API Call #3: verify_all_genes（verify_response.py）

**代码**: `registry.call_tool("verify_all_genes")` — 强制调用

| 输入 | 输出 |
|------|------|
| MD 原文 + extraction JSON | 每个基因每个字段的 SUPPORTED/UNSUPPORTED/UNCERTAIN |

handler `handle_verify_all()` 解析验证结果，存入 `state["verify_results"]`。

## 运行方式

```bash
bash scripts/run.sh pipeline           # 全量
bash scripts/run.sh pipeline-test      # 测试第 1 个
bash scripts/run.sh pipeline-test 3    # 测试第 3 个
```

## 常见故障排查

### 1. classify 返回空基因列表
代码会打印 `⚠️ classify 返回空基因列表`，跳过 API #2。检查 MD 文件是否有 Results 部分。

### 2. JSON 截断
`ToolRegistry._repair_truncated_json()` 自动修复。

### 3. 字符串数组（基因是字符串而非对象）
`handlers.py` 中的 `_handle_extract()` 自动检测并修复。

### 4. 添加新 tool
1. 在本文件 YAML 的 `tools:` 下添加 tool 定义
2. 在 `handlers.py` 中添加对应的 handler 函数
3. 在 `md_to_json.py` 或 `verify_response.py` 中用 `call_tool()` 硬编码调用
