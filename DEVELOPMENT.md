# NutriMaster 协作开发与维护指南

本文档面向后续参与 NutriMaster 开发、数据维护和部署的协作者。README 负责快速了解和启动项目；本文档负责说明如何安全地改代码、改数据、跑测试、排查问题和维护长期演进。

## 一句话原则

NutriMaster 的核心资产是 `data/corpus/` 中的 verified JSON 主语料，以及围绕它构建的抽取、验证、索引和问答链路。开发时优先保护主语料一致性、配置路径一致性和索引可重建性。

## 推荐工作流

1. 从最新分支创建开发分支。
2. 确认本地环境和 `.env`。
3. 根据改动范围跑最小测试。
4. 修改代码或数据。
5. 重新跑相关测试和 lint/语法检查。
6. 检查 `git diff`，确保没有混入个人数据、密钥、临时文件和无关大文件。
7. 提交前写清楚变更目的、影响范围和验证方式。

建议分支命名：

```text
feature/<short-topic>
fix/<short-topic>
refactor/<short-topic>
data/<short-topic>
docs/<short-topic>
```

示例：

```bash
git switch -c docs/development-guide
git switch -c fix/corpus-output-dir
git switch -c refactor/retrieval-settings
```

## 模块边界

### `src/nutrimaster/extraction/`

负责从 Markdown 论文生成 verified JSON。

主要文件：

- `src/nutrimaster/extraction/config.py`：读取环境变量并确定输入、输出、prompt、schema、报告目录。
- `src/nutrimaster/extraction/extract.py`：调用 LLM 完成初始抽取。
- `src/nutrimaster/extraction/verify.py`：基于原文验证和修正字段。
- `src/nutrimaster/extraction/pipeline.py`：编排单篇和批量处理。
- `src/nutrimaster/extraction/run.sh`：推荐的 shell 入口，默认输出到 `data/corpus/`。

维护规则：

- 新 verified JSON 必须写入 `data/corpus/`。
- 修改 schema 后，要同步检查 prompt、验证逻辑、chunking 逻辑和相关测试。
- `src/nutrimaster/extraction/config.py` 在 import 时读取环境变量，涉及路径的设置必须发生在 import 之前。
- 大批量抽取会消耗 LLM token，运行前确认 `MODEL`、`OPENAI_BASE_URL`、`MAX_WORKERS` 和 `JSON_DIR`。

### `src/nutrimaster/config/`

负责统一配置。

主要入口：

- `nutrimaster.config.settings.Settings.from_env()`
- `nutrimaster.config.settings.RagSettings`

维护规则：

- 新增运行配置时，优先放到 `Settings` 或对应子 settings 中。
- 不要在业务代码里散落读取环境变量，除非是非常局部、一次性的启动行为。
- 默认主语料目录是 `data/corpus/`。
- `RAG_INDEX_DIR` 和 `RAG_PERSONAL_LIB_DIR` 仍位于 `data/index/` 和 `data/personal_lib/`。

### `src/indexing/`

负责从主语料生成检索 chunk 和索引。

主要文件：

- `indexing/chunking.py`：根据不同 gene bucket 构造检索 chunk。
- `indexing/incremental_indexer.py`：基于 manifest 做增量索引。
- `indexing/index_service.py`：索引构建服务边界。

维护规则：

- 索引器只应扫描 `*_nutri_plant_verified.json`。
- 修改 chunk 字段、chunk 类型或路由逻辑后，要更新对应单元测试。
- `manifest.json` 记录的是文件 hash 和 chunk range；如果 chunker 行为不兼容，应更新 `CHUNKER_VERSION`。
- `chunks.pkl` 和 `embeddings.npy` 是生成物，不要把大索引二进制作为常规代码改动提交。

### `src/retrieval/`

负责检索、embedding、重排、个人库和查询翻译。

维护规则：

- 调用 Jina 的代码需要处理 API key 缺失和外部服务失败。
- 个人库索引与全局索引分开，不要混写到 `data/index/`。
- 检索结果格式会影响 agent tools 和前端展示，改动时要检查工具契约测试。

### `src/nutrimaster/web/`

负责 Web、认证、Admin 挂载和前端静态资源。

主要入口：

- `uv run nutrimaster web`
维护规则：

- `nutrimaster.web.app` 是完整 Web 应用，会挂载 Admin 到 `/admin`。
- 不再维护 Headless API；自动化测试直接打主 Web app。
- 修改 API 响应格式时，优先添加或更新行为测试。
- 认证和用户信息依赖 Supabase，相关测试要区分单元测试和真实服务集成测试。

### `src/nutrimaster/web/admin/`

负责管理后台。

主要入口：Web 应用中的 `/admin`

维护规则：

- Admin 会在 import nutrimaster.extraction 前设置 `JSON_DIR`、`PROMPT_PATH` 和 `SCHEMA_PATH`，不要随意改变这个顺序。
- 上传和已处理列表应只关注 `*_nutri_plant_verified.json`。
- 重建索引前确认 `DATA_DIR` 指向 `data/corpus/`。
- 管理员权限由 `ADMIN_EMAIL` 白名单控制。

### `src/agent/`、`src/tools/`、`src/skills/`

负责 Agent runtime、工具调用和系统技能。

维护规则：

- 新增工具时，要明确工具输入输出结构，并补充工具契约测试。
- 技能内容应与工具能力保持一致。
- 用户自定义技能位于 `data/user_skills/`，属于运行时数据，不应提交。

### `src/crispr/`

负责 CRISPR 靶点设计、accession 查询、实验方案和 SOP 模板。

维护规则：

- 模板位于 `src/crispr/templates/`，属于包数据。
- 修改 SOP 模板时，要检查 Web 端生成结果是否仍能被前端消费。
- 涉及外部生物数据库请求时，要区分真实服务测试和本地单元测试。

## 数据维护规则

### 主语料

主语料目录：

```text
data/corpus/
```

文件命名：

```text
<paper_stem>_nutri_plant_verified.json
```

维护要求：

- 不要把旧 schema 的数字命名 JSON 放回 `data/` 或 `data/corpus/`。
- 不要把临时抽取结果放进主语料。
- 如果手动编辑 verified JSON，必须保证 JSON 格式合法，并保留核心字段。
- 大批量更新主语料后，需要重建或增量更新索引。

### 索引

索引目录：

```text
data/index/
```

常见文件：

```text
manifest.json
chunks.pkl
embeddings.npy
```

维护要求：

- `manifest.json` 可提交用于描述当前索引状态，但要注意它和语料版本的一致性。
- `.pkl` 和 `.npy` 通常是大文件/生成物，不作为常规代码改动提交。
- 索引出问题时，优先删除或忽略旧二进制索引，然后重新构建。

### 用户数据

用户数据目录：

```text
data/personal_lib/
data/user_skills/
```

维护要求：

- 这些目录属于运行时用户数据，默认不应提交。
- 不要把用户上传 PDF、个人 index、用户自定义 skill 混入代码提交。
- 处理 bug report 时，如果需要样例数据，应构造最小匿名 fixture。

## 常见开发任务

### 修改抽取 schema

1. 修改 `src/nutrimaster/extraction/prompts/nutri_gene_schema_v5.json`。
2. 同步检查 `src/nutrimaster/extraction/prompts/nutri_gene_prompt_v5.txt`。
3. 检查 `src/nutrimaster/extraction/verify.py` 是否依赖字段名。
4. 检查 `src/indexing/chunking.py` 是否需要消费新字段。
5. 添加或更新 schema/验证/chunking 测试。
6. 用 1 篇论文跑 `pipeline-test`。
7. 检查输出 JSON 和 token report。

推荐验证：

```bash
uv run pytest src/nutrimaster/extraction/tests -q
uv run pytest tests/unit/test_chunking_contract.py -q
uv run nutrimaster extract --test 1
```

### 修改 RAG chunking 或索引逻辑

1. 先添加或更新 `tests/unit/test_chunking_contract.py`、`test_indexer_*` 或 `test_index_service_contract.py`。
2. 修改 `src/indexing/`。
3. 如果 chunk 格式不兼容，更新 `CHUNKER_VERSION`。
4. 用小样本构建索引。
5. 检查检索工具测试。

推荐验证：

```bash
uv run pytest tests/unit/test_chunking_contract.py -q
uv run pytest tests/unit/test_index_service_contract.py tests/unit/test_indexer_consistency.py -q
```

### 修改 Web API

1. 明确主 Web app 的接口行为。
2. 更新 `nutrimaster.web` 下对应模块。
3. 更新相关行为测试。
4. 如果前端静态文件依赖响应字段，同步检查 `src/nutrimaster/web/static/`。

推荐验证：

```bash
uv run pytest tests/unit -q
```

### 修改 Admin 行为

1. 保持路径设置在 import nutrimaster.extraction 之前。
2. 上传、列表、去重逻辑只使用 `*_nutri_plant_verified.json`。
3. 涉及 pipeline 运行时，检查 SSE event 名称和前端 `admin.js` 是否匹配。
4. 涉及索引重建时，确认 `DATA_DIR` 为 `data/corpus/`。

推荐验证：

```bash
uv run pytest tests/unit -q
uv run nutrimaster web
```

### 修改配置

1. 修改 `src/nutrimaster/config/settings.py`。
2. 更新 `.env.example`，不要写真实密钥。
3. 更新 README 和本文档中对应配置说明。
4. 更新 `tests/unit/test_rag_settings_contract.py` 或新增配置测试。

推荐验证：

```bash
uv run pytest tests/unit/test_rag_settings_contract.py -q
uv run nutrimaster check-config
```

## 测试策略

按改动范围选择测试，不要只依赖手工试跑。

快速单元测试：

```bash
uv run pytest tests/unit -q
```

Extractor 测试：

```bash
uv run pytest src/nutrimaster/extraction/tests -q
```

跳过外部服务：

```bash
uv run pytest -m "not integration and not e2e"
```

真实服务集成测试：

```bash
uv run pytest -m integration
```

浏览器 e2e：

```bash
uv run pytest -m e2e
```

脚本语法检查：

```bash
bash -n src/nutrimaster/extraction/run.sh
```

## 提交前检查清单

提交前至少检查：

- `git status` 中没有意外文件。
- 没有提交 `.env`、密钥、token、服务账号、真实用户资料。
- 没有提交个人 PDF、个人库索引、用户 skill。
- 新 generated JSON 确实属于 `data/corpus/` 主语料。
- 根目录 `data/` 下没有散落的旧 JSON。
- 相关测试已运行，并记录命令和结果。
- README/DEVELOPMENT 与代码路径一致。

常用检查命令：

```bash
git status --short
git diff --stat
uv run pytest -m "not integration and not e2e"
```

如果只是文档改动，至少运行：

```bash
bash -n src/nutrimaster/extraction/run.sh
uv run pytest tests/unit/test_rag_settings_contract.py -q
```

## 排查指南

### 新抽取 JSON 写到了错误目录

检查：

```bash
echo "$JSON_DIR"
python - <<'PY'
from nutrimaster.extraction.config import OUTPUT_DIR
print(OUTPUT_DIR)
PY
```

期望输出应指向 `data/corpus/`。如果不是，检查 `.env`、shell 环境变量和 Admin import 顺序。

### Web 启动后没有检索结果

检查：

- `RAG_DATA_DIR` 是否指向 `data/corpus/`
- `data/corpus/` 是否有 `*_nutri_plant_verified.json`
- `data/index/` 是否有有效索引
- `JINA_API_KEY` 是否配置
- 是否需要重建索引

### Admin 无法访问

检查：

- `ADMIN_EMAIL` 是否包含当前登录邮箱
- Supabase service role key 是否配置
- Web 中访问 `/admin` 是否命中主服务挂载的 Admin

### 外部服务测试失败

先确认失败类别：

- LLM key/base URL/model 是否正确
- Jina key 是否正确
- Supabase URL/service role/anon key 是否正确
- 本地网络和代理是否可访问对应服务

如果只是本地开发，不要为了通过测试而改业务逻辑；可以先使用 `uv run pytest -m "not integration and not e2e"`。

## 文档维护规则

- README 面向新用户和快速启动。
- `DEVELOPMENT.md` 面向协作者和长期维护。
- 配置、路径、命令、数据目录发生变化时，两个文档都要检查。
- 文档示例命令必须能和当前代码默认行为一致。
- 项目名称统一写作 NutriMaster；运行相关代码、文档和命令不再使用旧项目名。

## 当前约定摘要

- 项目名：NutriMaster
- Python 包名：`nutrimaster`
- 主语料：`data/corpus/`
- 全局索引：`data/index/`
- 个人库：`data/personal_lib/`
- 用户技能：`data/user_skills/`
- Web 入口：`uv run nutrimaster web`
- Admin 入口：`/admin`
- Extractor 入口：`uv run nutrimaster extract`
- 配置入口：`nutrimaster.config.settings.Settings.from_env()`
