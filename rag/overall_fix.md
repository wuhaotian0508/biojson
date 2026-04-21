# Overall Fix Report

> 本次重构参照 EvoMaster 项目的成熟模式，对 RAG 系统进行了工具基类、上下文管理和并发安全三项改进。

---

## 已完成的改进

### 1. Tool 基类 + 自动发现（参照 EvoMaster `BaseTool` + `ToolRegistry`）

**问题**: 8 个工具类通过鸭子类型实现 `name/description/schema/execute`，无接口约束，新工具容易漏实现方法。

**修复**:
- **新增 `tools/base.py`**: `BaseTool` ABC，强制 `name`/`description` ClassVar + `schema` property + `async execute()` 方法。附带 `ToolError` 异常类。
- **改进 `tools/registry.py`**: `register()` 增加 `isinstance(tool, BaseTool)` 校验 + 重复注册警告。新增 `auto_discover()` 方法自动扫描 `tools/*.py` 注册无参构造的工具。
- **迁移所有 8 个工具**: 添加 `(BaseTool)` 继承，无逻辑变更。

**影响文件**:
- `tools/base.py` (新建)
- `tools/registry.py` (重写)
- `tools/__init__.py` (导出 BaseTool)
- `tools/pubmed_search.py`, `gene_db_search.py`, `personal_lib_search.py`, `rag_search.py`, `crispr_tool.py`, `read.py`, `write.py`, `shell.py` (添加继承)

---

### 2. 上下文管理三层防御（参照 EvoMaster `ContextManager`）

**问题**: Agent 对话循环中 `messages` 无限增长，工具结果动辄数千字，5 轮工具调用后就可能超过模型 128K 上下文窗口导致 API 报错。

**修复 — 新增 `core/context.py`**:

| 层级 | 触发条件 | 动作 |
|------|----------|------|
| L1 轻量裁剪 | tokens >= 80% usable | 替换保护区外的旧 tool 输出为 `"[已清理旧工具输出]"` |
| L2 摘要压缩 | tokens >= 95% usable | 用 LLM 生成结构化对话摘要替换旧消息（失败则降级 L1） |
| L3 紧急截断 | API 返回 context overflow | 保留 system + 最近 5 条消息，重试 |

**额外防护**:
- `cap_tool_output()`: 单个工具输出超 15,000 字符时保留首尾各 7.5K
- Token 估算采用字符法（len/4）+ API usage 增量修正 + 5% 安全系数
- `is_overflow_error()`: 正则检测 API 错误中的 context overflow 关键词

**集成到 `core/agent.py`**:
- 每次 `call_llm` 前调用 `context_mgr.prepare()` 按需压缩
- 工具结果注入前执行 `cap_tool_output()` 截断
- `call_llm` 异常时检测 overflow 并自动恢复

**影响文件**:
- `core/context.py` (新建)
- `core/agent.py` (修改: 导入 ContextManager, __init__ 创建实例, run() 循环集成)

---

### 3. 并发安全修复

**问题**: `PersonalLibSearchTool._current_user_id` 和 `RAGSearchTool._current_user_id` 是类属性，在 uvicorn `--workers 4` 下同一 worker 内并发请求会互相覆盖 user_id。

**修复**: 
- 删除 `_current_user_id` 类属性
- 在 tool 的 `schema` 中添加 `user_id` 参数
- 在 `execute()` 方法中通过参数接收 `user_id`
- Agent 在 `registry.execute()` 时统一注入 `user_id=user_id`
- `app.py` 不再设置类属性

**影响文件**:
- `tools/personal_lib_search.py` (删除 _current_user_id, execute 加 user_id 参数)
- `tools/rag_search.py` (同上)
- `core/agent.py` (execute 调用注入 user_id)
- `web/app.py` (删除 _current_user_id 注入行)

---

## 遗留问题 & 建议

### P0 — 应尽快修复

1. **测试全部失效**: `tests/` 下 4 个测试文件引用 pre-refactor 路径（`rag.config` → `core.config`, `SkillLoader` → `Skill_loader`）。需更新 import 路径。

### P1 — 建议改进

2. **Harness 沙箱范围过窄**: `check_path()` 仅允许 `skills/` 下的路径，但 Agent 可能需要读取数据文件。建议扩展白名单或按用户角色配置。

3. **Memory 模块未接入**: `memory/` 包（MemoryManager, MemoryStore）已完整实现但未在 `web/app.py` 或 Agent 中使用。

4. **CRISPR pipeline 中的顺序 HTTP 请求**: `crispr_target.py` 对每条序列逐个发 HTTP 请求（串行 for 循环），可改为 `asyncio.gather` 并行。

### P2 — 可选优化

5. **Config Pydantic 化**: 当前 `core/config.py` 用模块级常量，无验证。可参照 EvoMaster 的 `EvoMasterConfig` 改为 Pydantic `BaseModel` 嵌套结构。

6. **执行轨迹持久化**: EvoMaster 每步增量保存到 JSON（线程安全锁）。当前 Agent 的工具调用和结果仅通过 SSE 输出，无法事后复盘。建议保存完整 trajectory 到日志。

7. **代码风格统一**: `read.py`/`write.py`/`shell.py` 风格（无空格、无 docstring）与其他模块不一致。已在本次重构中改善缩进和 `**_` 参数。

### 关于 asyncio vs multiprocessing

经分析，项目几乎全是 I/O 密集型（Jina API 嵌入/重排、LLM API、PubMed API、NCBI API），本地 CPU 计算（numpy cosine sim、regex、PDF 提取）均为轻量级。64 核服务器上 multiprocessing 无额外收益，asyncio 是正确选择。`run_prod.sh` 的 4 workers 已足够。

---

## 验证结果

- [x] `from tools.base import BaseTool` — OK
- [x] 8 个工具全部通过 `issubclass(cls, BaseTool)` 检查
- [x] `auto_discover()` 正确注册 6 个无参工具，跳过 2 个需构造参数的
- [x] `from core.context import ContextManager` — OK
- [x] L1 裁剪：20 条旧 tool 输出 → 全部替换为占位符
- [x] `cap_tool_output()`: 20K 字符 → 截断到 ~15K
- [x] `is_overflow_error()`: 正确识别 overflow 错误
- [x] `emergency_truncate()`: 21 条 → 6 条（保留 system + 最近 5 条）
- [x] `uvicorn app:app` 启动无报错，health check 200
- [x] 全部 8 个工具正常注册
