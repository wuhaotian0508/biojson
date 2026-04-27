# DeepSeek V4 兼容性适配说明

## 概述

本次更新为 BioJSON 项目添加了对 DeepSeek V4 的完整支持，包括其新发布的 thinking mode 特性。

## 主要改动

### 1. RAG 系统 (`rag/core/llm_client.py`)

#### 新增模型识别
- 添加 `deepseek-v4` 到支持的 reasoner 模型列表
- 更新模型识别逻辑，支持 V3.2/V4/R1 全系列

#### 参数处理增强
```python
def _sanitize_params_for_model(model_name: str, params: dict, is_agent_call: bool = False)
```

**新增功能：**
- 自动移除 DeepSeek thinking 模式下不兼容的参数：
  - `temperature`, `top_p`, `presence_penalty`, `frequency_penalty` (会被忽略)
  - `logprobs`, `top_logprobs` (会报 400 错误)

- 通过 `extra_body` 自动配置 thinking 模式：
  ```python
  extra_body = {
      "thinking": {"type": "enabled"},  # 默认开启 thinking
      "reasoning_effort": "high" | "max"  # 根据场景自动选择
  }
  ```

- **智能 effort 选择：**
  - Agent 多轮工具调用：自动使用 `"max"` effort（复杂任务）
  - 普通单次调用：使用 `"high"` effort（平衡性能和成本）

#### API 函数更新
所有 LLM 调用函数新增 `is_agent_call` 参数：
- `call_llm(messages, tools, model_id, is_agent_call=False, **kwargs)`
- `call_llm_stream(messages, model_id, is_agent_call=False, **kwargs)`
- `call_llm_sync(messages, is_agent_call=False, **kwargs)`

### 2. Agent 系统 (`rag/core/agent.py`)

所有 Agent 内部的 LLM 调用都传递 `is_agent_call=True`：
```python
msg = await self.call_llm(
    messages,
    tools=tool_definitions,
    model_id=model_id,
    temperature=0.3,
    is_agent_call=True,  # 自动使用 max effort
)
```

**影响范围：**
- 主工具调用循环
- L3 紧急截断重试
- 流式回答生成
- Function call 泄露检测后的重试

### 3. Extractor 系统 (`extractor/`)

#### 新增工具函数 (`extractor/utils.py`)
```python
def is_deepseek_model(model_name: str) -> bool
def prepare_deepseek_params(model_name: str, params: dict) -> dict
```

**特点：**
- 与 RAG 系统保持一致的参数处理逻辑
- Extractor 使用 `"high"` effort（单次提取任务）
- 自动移除不兼容参数，添加 `extra_body` 配置

#### 更新文件
- `extractor/extract.py`: 提取 API 调用前处理参数
- `extractor/verify.py`: 验证 API 调用前处理参数

### 4. reasoning_content 处理

**已有功能（保持不变）：**
- Agent 在同一轮工具调用循环内保留 `reasoning_content`（DeepSeek API 要求）
- 新一轮对话开始时自动清理旧的 `reasoning_content`（节省 token）
- 流式输出时跳过 `reasoning_content`（不展示给用户）

## 使用方法

### 配置 DeepSeek V4

在 `.env` 文件中配置：

```bash
# 主模型使用 DeepSeek V4
MODEL=deepseek-v4
OPENAI_API_KEY=your-deepseek-api-key
OPENAI_BASE_URL=https://api.deepseek.com/v1

# 或作为备用模型
FALLBACK_MODEL=deepseek-v4
FALLBACK_API_KEY=your-deepseek-api-key
FALLBACK_BASE_URL=https://api.deepseek.com/v1
```

### 自动行为

**无需任何代码修改**，系统会自动：

1. **识别模型**：检测到 `deepseek-v4` 后自动启用兼容模式
2. **清理参数**：移除 `temperature` 等不兼容参数
3. **配置 thinking**：通过 `extra_body` 传递 thinking 配置
4. **选择 effort**：
   - RAG Agent 多轮调用 → `max` effort
   - Extractor 单次提取 → `high` effort
   - 普通查询 → `high` effort

### 手动控制 thinking 模式（可选）

如果需要手动控制，可以通过 `extra_body` 传递：

```python
# 禁用 thinking
response = await call_llm(
    messages,
    extra_body={"thinking": {"type": "disabled"}}
)

# 强制使用 max effort
response = await call_llm(
    messages,
    extra_body={"reasoning_effort": "max"}
)
```

## 兼容性

### 向后兼容
- 非 DeepSeek 模型（GPT-4, Claude 等）完全不受影响
- 现有代码无需修改即可使用 DeepSeek V4
- 所有参数处理都是增量式的，不会破坏现有功能

### 测试覆盖
运行测试验证兼容性：
```bash
python test_deepseek_v4_compat.py
```

测试内容：
- ✅ 模型识别（V3.2/V4/R1）
- ✅ 参数清理（移除不兼容参数）
- ✅ extra_body 配置（thinking + reasoning_effort）
- ✅ Agent vs 普通模式的 effort 选择
- ✅ 非 DeepSeek 模型不受影响

## 性能影响

### Token 消耗
- **thinking mode 开启**：会增加 reasoning_content 的 token 消耗
- **自动清理**：新对话轮次自动移除旧 reasoning_content，减少浪费
- **流式输出**：reasoning_content 不发送给用户，节省带宽

### 推理质量
- **Agent 模式 (max effort)**：复杂多轮工具调用，推理质量最高
- **Extractor (high effort)**：单次提取任务，平衡质量和成本
- **普通查询 (high effort)**：日常问答，性能充足

## 参考文档

- DeepSeek V4 API 文档：https://api-docs.deepseek.com/zh-cn/guides/thinking_mode
- 关键特性：
  - thinking 模式默认开启
  - reasoning_effort: high (默认) | max (复杂任务)
  - 不支持 temperature/top_p 等参数
  - 工具调用时必须回传 reasoning_content

## 更新日期

2025-04-24
