# BioJSON Admin Panel 使用说明

## 概述

Admin Panel 是一个独立的 Web 管理后台（端口 5001），用于管理论文提取 pipeline 的完整生命周期：

```
上传 zip → 预览首篇 → 批量处理 → 自动入库 RAG
```

## 启动

### 前置要求

确保 `.env` 文件中配置了以下变量：

```bash
# 必需 — API
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://xxx/v1

# 必需 — 认证
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
ADMIN_EMAIL=your-admin@example.com    # 只有此邮箱可访问 admin

# 可选 — 模型
MODEL=Vendor2/Claude-4.6-opus
```

### 启动命令

```bash
bash admin/run.sh
```

服务启动后访问 **http://localhost:5001**

> Admin Panel 运行在端口 5001，不会影响 RAG Web App（端口 5000）。

---

## 功能说明

### 1. Dashboard

显示三个统计卡片：

| 卡片 | 含义 |
|------|------|
| **Input Queue** | `extractor/input/` 中待处理的 .md 文件数量 |
| **Processed** | `rag/data/` 中已完成的 verified JSON 数量 |
| **Archive** | `extractor/input/processed/` 中已归档的 .md 数量 |

如果 pipeline 正在运行，顶部会显示蓝色进度横幅。

### 2. Upload

上传包含 .md 文件的 **zip 压缩包**。

**操作步骤**：
1. 拖拽 zip 文件到上传区域，或点击选择文件
2. 系统自动解压并执行去重检查
3. 显示结果：新增文件数、跳过文件数及原因

**去重规则**：
- 如果 `rag/data/` 中已有 `{stem}_nutri_plant_verified.json` → 跳过（标记"已在库中"）
- 如果 `extractor/input/` 中已有同名 .md → 跳过（标记"已在队列中"）
- 通过检查的文件写入 `extractor/input/`

### 3. Pipeline

核心处理面板，有三种状态：

#### 空闲态
- 显示待处理文件数量
- 两个按钮：**Preview First Paper** / **Run All**

#### Preview（预览）
点击 **Preview First Paper** 后：
1. 同步处理 input 中排序第一个 .md（耗时 2-5 分钟）
2. 处理完成后页面显示生成的 verified JSON
3. 确认格式正确后，点击 **Run Remaining** 处理剩余文件

> 预览是真实处理 —— .md 会移入 processed 目录，JSON 会写入 `rag/data/`。

#### Run（批量运行）
点击 **Run All** 或 **Run Remaining** 后：
1. 后台线程逐篇处理剩余 .md 文件
2. 页面通过 SSE 实时显示进度条、当前文件、完成日志
3. 全部完成后自动重建 RAG 向量索引
4. 可随时点击 **Stop** 停止（当前论文处理完后停止）

> 处理完成后需要 **重启 RAG Web App** (`rag/web/app.py`) 才能使新索引在内存中生效。

### 4. Papers

表格显示 `rag/data/` 中所有已处理的论文：

| 列 | 内容 |
|----|------|
| # | 序号 |
| Title | 从 JSON 中读取的论文标题 |
| Filename | JSON 文件名 |
| Modified | 最后修改时间 |

### 5. Prompt / Schema Editor

在线编辑提取使用的 prompt 和 schema 文件：

- **Prompt** tab — 编辑 `extractor/prompts/nutri_gene_prompt_v5.txt`
- **Schema** tab — 编辑 `extractor/prompts/nutri_gene_schema_v5.json`

保存后会自动清除 `lru_cache`，下一次 pipeline 处理将使用新版本。

> Schema 保存前会验证 JSON 格式，格式错误会阻止保存。

---

## 典型工作流

```
步骤 1:  Upload tab     → 上传包含论文 .md 的 zip
步骤 2:  Pipeline tab   → 点击 "Preview First Paper" 预览
步骤 3:  确认 JSON 格式 OK → 点击 "Run Remaining" 批量处理
步骤 4:  观察 SSE 进度    → 等待全部完成 + 索引重建
步骤 5:  重启 RAG web app → 新数据可被检索
```

---

## 安全

- 所有 API 路由（除 `/api/config`）都需要 Supabase 登录 token
- 必须使用 `ADMIN_EMAIL` 环境变量指定的邮箱登录，其他账号返回 403
- SSE 端点通过 URL query param `?token=xxx` 传递认证（EventSource 不支持自定义 header）

---

## 文件结构

```
admin/
├── app.py              # Flask 后端（端口 5001）
├── __init__.py         # Python 包标记
├── run.sh              # 启动脚本
└── static/
    ├── index.html      # SPA 页面（5 个 tab）
    ├── style.css       # 深色 lab-console 主题
    └── admin.js        # 前端逻辑（认证、上传、SSE、编辑器）
```

不修改任何 `rag/web/` 或 `extractor/` 中的现有文件。
