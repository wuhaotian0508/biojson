# 重构报告

## 概述

本次重构对 `rag/` 目录进行了 5 项改动：模块迁移、安全沙箱集成、文件清理、新增 PubMed skill。

---

## 1. Harness 安全沙箱集成

**改动文件**: `tools/read.py`、`tools/write.py`、`tools/shell.py`

`core/harness.py` 提供了 `check_path()` 和 `check_command()` 两个安全检查函数，
限制 Agent 工具只能操作 `skills/` 目录（不含 `skill-creator/`），并阻止使用 `..` 路径穿越。

- `read.py` / `write.py`：在 `execute()` 开头调用 `check_path(file_path)`
- `shell.py`：在 `execute()` 开头调用 `check_command(command)`

这意味着当 Agent 的 LLM 尝试读写 skills 目录之外的文件、或执行包含 `..` 或 `skill-creator` 的命令时，
会立即抛出 `PermissionError`，阻止操作执行。

---

## 2. 核心模块迁移到 core/

**迁移的文件**:

| 原位置 | 新位置 |
|--------|--------|
| `rag/config.py` | `rag/core/config.py` |
| `rag/agent.py` | `rag/core/agent.py` |
| `rag/llm_client.py` | `rag/core/llm_client.py` |

**路径修正**:
- `core/config.py` 中的 `BASE_DIR`、`PROJECT_ROOT`、`.env` 路径计算增加了一层 `parent`（因为多了 `core/` 目录层级）
- `core/llm_client.py` 的 config 导入改为 `from core.config import ...`

**全量 import 更新**（共 20 处）:
- 16 个文件的 `from config import` / `import config` → `from core.config import` / `import core.config as config`
- 3 个文件的 `from llm_client import` → `from core.llm_client import`
- 1 个文件的 `from agent import` → `from core.agent import`

涉及文件: `pipeline.py`、`generation/generator.py`、`search/`（5 个文件）、`utils/`（3 个文件）、
`web/`（5 个文件）、`tools/pubmed_search.py`、`skills/crispr_experiment/pipeline.py`

**保留**: `rag/data_loader.py` 是 pickle 反序列化兼容 shim（`from utils.data_loader import *`），保持不动。

---

## 3. pipeline.py / generator.py / tools / skills 关系说明

```
┌──────────────────────────────────────────────────────────┐
│                     web/app.py (入口)                     │
│  创建 Agent, Toolregistry, Skill_loader 实例并组装        │
└──────────┬───────────────────────────────────┬────────────┘
           │                                   │
           ▼                                   ▼
  ┌─────────────────┐               ┌─────────────────────┐
  │   core/agent.py │               │  pipeline.py (legacy)│
  │   (当前使用)     │               │  + generator.py      │
  │                 │               │  (已被 Agent 替代)    │
  └────────┬────────┘               └──────────────────────┘
           │
           │  LLM 决定调用哪些 tools
           ▼
  ┌─────────────────┐
  │  tools/          │  Toolregistry 管理
  │  ├ pubmed_search │  每个 tool: name + schema + execute()
  │  ├ gene_db_search│
  │  ├ crispr_tool   │
  │  ├ read/write    │
  │  └ shell         │
  └─────────────────┘
           ▲
           │  skill.md 声明可用 tools
           │
  ┌─────────────────┐
  │  skills/         │  Skill_loader 扫描
  │  ├ rag-answer    │  每个 skill: skill.md (YAML + Markdown)
  │  ├ pubmed-database│ 声明 name/description/tools
  │  ├ crispr-experiment│
  │  └ skill-creator │
  └─────────────────┘
```

**关键区别**:
- **pipeline.py + generator.py** (legacy): 固定流程 search→rerank→generate，由代码硬编码调用顺序
- **agent.py** (active): LLM 驱动的循环，Agent 自主决定调用哪些 tools、调用几次、以什么顺序
- **tools**: 统一接口的工具类，被 Agent 或 Pipeline 通过 Toolregistry 调度
- **skills**: Markdown 指令文件，告诉 Agent 在特定场景下该怎么使用 tools

---

## 4. 清理 rag/.gitignore

**删除**: `rag/.gitignore`（与根 `.gitignore` 大量重复）

**合并到根 `.gitignore`**: 添加 `rag/personal_lib/`（唯一需要保留的独有条目）

`rag/web/requirements.txt` 已在之前删除（只含 flask+gunicorn，已在根 `requirements.txt` 中）。

---

## 5. 新增 PubMed Skill

**位置**: `rag/skills/pubmed-database/skill.md`

**参考来源**:
- [K-Dense-AI/claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills) — paper-lookup 中的 PubMed 参考
- [SkillsMP PubMed Database Skill](https://skillsmp.com/) — 独立 PubMed 技能的 9 项核心能力

**内容**: 面向项目的 PubMed 搜索最佳实践，包含：
- 搜索时机判断
- 英文查询构建指南
- 高级搜索语法（MeSH 术语、字段限定、布尔运算、日期过滤）
- 分步搜索策略
- PICO 框架（系统性综述）
- 常用查询模板（维生素、矿物质、氨基酸、类胡萝卜素、基因编辑）

---

## 改动后的 core/ 目录结构

```
rag/core/
├── __init__.py       # 包初始化
├── config.py         # 全局配置（路径、API、检索参数）
├── agent.py          # LLM 工具调用 Agent
├── llm_client.py     # LLM 网关（主/备切换、同步/异步）
├── harness.py        # 安全沙箱（路径/命令检查）
└── REPORT.md         # 本报告
```
