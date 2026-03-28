# Agent Skills Demo 详解

> 对应源码：`self-learn/agent-skills-demo.py`

## 一、概述

这个脚本是一个 **最简化的 Agent Skills 智能体**示例。它展示了如何用不到 120 行 Python 代码实现 Agent Skills 的核心机制——**渐进式披露（Progressive Disclosure）**：

1. 启动时只加载每个 Skill 的 **元数据**（name + description），消耗极少 token
2. 当用户请求匹配某个 Skill 时，模型 **主动调用工具** 读取完整的 SKILL.md
3. 读取到详细指令后，模型按照指令来回答用户

整个流程体现了 Agent Skills 的核心设计理念：**连接时轻量，使用时按需加载**。

### 运行前提

```bash
pip install anthropic pyyaml
export ANTHROPIC_API_KEY="你的密钥"
python self-learn/agent-skills-demo.py
```

需要在项目根目录下有 `skills/` 文件夹，且其中的子文件夹包含 `SKILL.md` 文件。

---

## 二、整体架构

```
┌─────────────────────────────────────────────────────────┐
│                      main() 主循环                       │
│                                                         │
│  用户输入 ──► Claude API ──► 判断是否需要调用工具        │
│                  │                                       │
│                  ├── stop_reason == "tool_use"           │
│                  │    └── 执行 read_file 读取 SKILL.md   │
│                  │         └── 带结果再次调用 Claude API  │
│                  │              └── 返回最终回答          │
│                  │                                       │
│                  └── stop_reason == "end_turn"           │
│                       └── 直接输出回答                   │
└─────────────────────────────────────────────────────────┘
```

**数据流简图：**

```
skills/
├── biojson-extraction/
│   └── SKILL.md          ◄── load_skill_list() 只读 frontmatter
├── another-skill/
│   └── SKILL.md
└── ...

         │
         ▼
   build_system_prompt()   ◄── 把 name+description 拼入 system prompt
         │
         ▼
   Claude API 调用         ◄── 模型根据 system prompt 判断匹配哪个 skill
         │
         ▼
   read_file 工具调用      ◄── 模型请求读取完整 SKILL.md（渐进式披露第二层）
         │
         ▼
   最终回答                ◄── 模型结合完整指令生成回复
```

---

## 三、逐函数详解

### 3.1 `load_skill_list(skills_dir)` —— 扫描技能元数据

```python
def load_skill_list(skills_dir: str) -> list[dict]:
    skills = []
    for name in os.listdir(skills_dir):
        skill_path = os.path.join(skills_dir, name, "SKILL.md")
        if not os.path.isfile(skill_path):
            continue
        # 解析 YAML frontmatter
        with open(skill_path, "r") as f:
            content = f.read()
        parts = content.split("---", 2)
        meta = yaml.safe_load(parts[1])
        skills.append({
            "name": meta["name"],
            "description": meta["description"],
            "path": skill_path,
        })
    return skills
```

**作用**：遍历 `skills/` 目录，找到每个子文件夹中的 `SKILL.md`，**只提取 YAML frontmatter 中的 `name` 和 `description`**。

**关键细节**：

| 步骤 | 说明 |
|------|------|
| `os.listdir(skills_dir)` | 列出 `skills/` 下的所有子文件夹名 |
| `os.path.join(skills_dir, name, "SKILL.md")` | 拼出每个 SKILL.md 的完整路径 |
| `content.split("---", 2)` | YAML frontmatter 格式为 `---\nyaml内容\n---\n正文`，按 `---` 分割后 `parts[1]` 就是 YAML 部分 |
| `yaml.safe_load(parts[1])` | 解析 YAML 得到字典，提取 `name` 和 `description` |

**为什么只取元数据？** 这就是渐进式披露的**第一层**——启动时只消耗约 100 token/skill，而不是把整个 SKILL.md 的几千 token 全塞进 system prompt。

**frontmatter 示例**（来自本项目的 `skills/biojson-extraction/SKILL.md`）：

```yaml
---
name: biojson-extraction
description: >
  BioJSON 论文基因提取项目的完整操作手册。当用户要求运行提取、验证、调试提取结果、
  修改 configs 中的 schema、排查"字符串数组"等提取质量问题、或修改 md_to_json.py /
  verify_response.py 时，使用此技能。
version: 1.0.0
tags: [biojson, extraction, llm, function-calling, schema, pipeline]
---
```

`split("---", 2)` 之后：
- `parts[0]` = `""` （空字符串，`---` 之前没内容）
- `parts[1]` = YAML 内容
- `parts[2]` = SKILL.md 的正文部分（此时被忽略）

---

### 3.2 `build_system_prompt(skills)` —— 构建系统提示词

```python
def build_system_prompt(skills: list[dict]) -> str:
    skill_xml = ""
    for s in skills:
        skill_xml += f"""
  <skill>
    <name>{s['name']}</name>
    <description>{s['description']}</description>
    <path>{s['path']}</path>
  </skill>"""

    return f"""你是一个有用的助手。你有一些可用的 skills。
当用户的请求匹配某个 skill 时，你必须先调用 read_file 工具读取对应的 SKILL.md，
然后严格按照里面的指令来回答。

<available_skills>{skill_xml}
</available_skills>"""
```

**作用**：将扫描到的技能列表拼接成 XML 格式，嵌入到系统提示词中。

**关键设计点**：

1. **XML 格式**：用 `<skill>`、`<name>`、`<description>`、`<path>` 标签包裹，Claude 对 XML 结构化数据的理解非常好，能准确地从中提取信息。

2. **包含 `path` 字段**：这是模型能够"自主读取"SKILL.md 的关键——system prompt 告诉模型文件路径，模型就知道该调用 `read_file` 读哪个文件。

3. **明确指令**："你必须先调用 read_file 工具读取对应的 SKILL.md"——这句话引导模型在匹配到 skill 后，主动发起工具调用，实现渐进式披露的**第二层**加载。

**生成的 system prompt 示例**：

```
你是一个有用的助手。你有一些可用的 skills。
当用户的请求匹配某个 skill 时，你必须先调用 read_file 工具读取对应的 SKILL.md，
然后严格按照里面的指令来回答。

<available_skills>
  <skill>
    <name>biojson-extraction</name>
    <description>BioJSON 论文基因提取项目的完整操作手册。当用户要求运行提取、验证...</description>
    <path>skills/biojson-extraction/SKILL.md</path>
  </skill>
</available_skills>
```

---

### 3.3 `TOOLS` 和 `handle_tool_call()` —— 工具定义与执行

```python
TOOLS = [
    {
        "name": "read_file",
        "description": "读取指定路径的文件内容",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"}
            },
            "required": ["path"],
        },
    }
]


def handle_tool_call(tool_name: str, tool_input: dict) -> str:
    if tool_name == "read_file":
        with open(tool_input["path"], "r") as f:
            return f.read()
    return "未知工具"
```

**作用**：定义一个 `read_file` 工具，让 Claude 能够读取本地文件。

**TOOLS 结构解析**：

| 字段 | 说明 |
|------|------|
| `name` | 工具名称，模型在回复中通过这个名字来调用工具 |
| `description` | 工具描述，帮助模型理解何时该用这个工具 |
| `input_schema` | JSON Schema 格式，定义工具的输入参数 |
| `input_schema.properties.path` | 唯一参数：文件路径 |
| `input_schema.required` | 必填参数列表 |

这个工具定义会随 API 请求一起发送给 Claude。当模型判断需要读取文件时，它会在回复中返回一个 `tool_use` 类型的 content block，包含 `name: "read_file"` 和 `input: {"path": "skills/xxx/SKILL.md"}`。

**`handle_tool_call` 函数**：是工具调用的实际执行器。当模型请求调用工具时，这个函数负责在本地文件系统上执行读取操作，并将结果返回给模型。

> **注意**：这里只实现了一个 `read_file` 工具。实际的 Agent Skills 框架（如 Claude Desktop）内置了更多工具。但这个最小示例表明：**只需一个 "读文件" 工具，就足以实现渐进式披露机制**。

---

### 3.4 `main()` —— 主循环（核心逻辑）

这是整个程序的入口和核心，我们拆开来分析。

#### 3.4.1 初始化阶段

```python
def main():
    client = anthropic.Anthropic()  # 需要设置 ANTHROPIC_API_KEY 环境变量

    skills = load_skill_list("skills")
    system_prompt = build_system_prompt(skills)

    print("=== System Prompt ===")
    print(system_prompt)
    print("=====================\n")

    messages = []
```

| 步骤 | 说明 |
|------|------|
| `anthropic.Anthropic()` | 创建 API 客户端，自动从 `ANTHROPIC_API_KEY` 环境变量读取密钥 |
| `load_skill_list("skills")` | 扫描 `skills/` 目录，提取所有技能的元数据 |
| `build_system_prompt(skills)` | 构建包含技能列表的系统提示词 |
| `messages = []` | 初始化对话历史（多轮对话的核心数据结构） |

#### 3.4.2 用户输入循环

```python
    while True:
        user_input = input("你: ")
        if user_input.lower() in ("quit", "exit"):
            break

        messages.append({"role": "user", "content": user_input})
```

标准的命令行交互循环。用户输入会被追加到 `messages` 列表中，作为对话历史的一部分。

#### 3.4.3 调用 Claude API

```python
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )
```

| 参数 | 说明 |
|------|------|
| `model` | 使用 Claude Sonnet 4 模型 |
| `max_tokens` | 最大输出 token 数 |
| `system` | 系统提示词（包含技能列表） |
| `tools` | 可用工具列表（`read_file`） |
| `messages` | 完整的对话历史 |

#### 3.4.4 工具调用循环（核心亮点）

```python
        while response.stop_reason == "tool_use":
            # 把模型的回复（含 tool_use）加入历史
            messages.append({"role": "assistant", "content": response.content})

            # 执行每个工具调用
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [读取 skill: {block.input.get('path', '')}]")
                    result = handle_tool_call(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "user", "content": tool_results})

            # 带着工具结果再次调用模型
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=system_prompt,
                tools=TOOLS,
                messages=messages,
            )
```

**这是整个脚本最核心的部分**，实现了 Anthropic Tool Use 的标准循环模式：

**循环条件**：`response.stop_reason == "tool_use"` 表示模型的回复中包含工具调用请求（而非直接的文本回答）。

**循环内部的步骤**：

```
第 1 步：模型回复包含 tool_use
  ┌──────────────────────────────────────┐
  │ response.content = [                 │
  │   TextBlock("我来读取这个技能..."),    │
  │   ToolUseBlock(                      │
  │     name="read_file",                │
  │     input={"path": "skills/.../SKILL.md"}, │
  │     id="toolu_xxx"                   │
  │   )                                  │
  │ ]                                    │
  └──────────────────────────────────────┘
           │
           ▼
第 2 步：将模型回复加入 messages（role: assistant）
           │
           ▼
第 3 步：遍历 content blocks，执行每个 tool_use
         handle_tool_call("read_file", {"path": "..."})
         → 返回 SKILL.md 的完整内容
           │
           ▼
第 4 步：构造 tool_result，加入 messages（role: user）
  ┌──────────────────────────────────────┐
  │ tool_results = [{                    │
  │   "type": "tool_result",             │
  │   "tool_use_id": "toolu_xxx",        │
  │   "content": "SKILL.md的完整内容..."  │
  │ }]                                   │
  └──────────────────────────────────────┘
           │
           ▼
第 5 步：带着工具结果再次调用 Claude API
         → 模型现在有了完整的 SKILL.md 内容
         → 可能直接回答（stop_reason="end_turn"）
         → 也可能继续调用其他工具（继续循环）
```

**为什么 tool_result 的 role 是 "user"？** 这是 Anthropic API 的设计约定。在对话历史中，assistant 和 user 必须交替出现。工具执行结果被视为"用户侧提供的信息"——因为工具是在客户端（用户侧）执行的，而非模型侧。

**`tool_use_id` 的作用**：每个工具调用都有唯一 ID（如 `toolu_xxx`），tool_result 通过这个 ID 与对应的 tool_use 匹配。这在模型同时调用多个工具时尤为重要。

#### 3.4.5 输出最终回复

```python
        final_text = "".join(
            block.text for block in response.content if block.type == "text"
        )
        messages.append({"role": "assistant", "content": response.content})
        print(f"AI: {final_text}\n")
```

当 `stop_reason` 不再是 `"tool_use"` 时（通常是 `"end_turn"`），表示模型已经给出了最终回答。从 response.content 中提取所有 `TextBlock` 的文本拼接输出。

---

## 四、完整执行流程示例

假设用户输入："帮我运行一下 biojson 的提取任务"

### 第一轮 API 调用

**发送给 Claude 的内容**：
- system: 包含 `<available_skills>` 列表（只有 name + description）
- messages: `[{"role": "user", "content": "帮我运行一下 biojson 的提取任务"}]`
- tools: `[read_file]`

**Claude 的判断**：用户请求匹配 `biojson-extraction` 技能（description 中提到"运行提取"），按照 system prompt 的指令，先读取 SKILL.md。

**Claude 返回**：
```json
{
  "stop_reason": "tool_use",
  "content": [
    {"type": "text", "text": "让我先读取相关技能的详细指令..."},
    {"type": "tool_use", "name": "read_file", "input": {"path": "skills/biojson-extraction/SKILL.md"}, "id": "toolu_abc123"}
  ]
}
```

### 工具执行

脚本在本地读取 `skills/biojson-extraction/SKILL.md`，获取完整内容（包含项目架构、数据流、命令说明、故障排查等数千 token 的详细指令）。

### 第二轮 API 调用

**发送给 Claude 的内容**：
- messages 现在包含：
  1. user: "帮我运行一下 biojson 的提取任务"
  2. assistant: [text + tool_use]
  3. user: [tool_result，包含 SKILL.md 完整内容]

**Claude 现在拥有了完整的领域知识**，可以根据 SKILL.md 中的具体指令来回答。

**Claude 返回**：
```json
{
  "stop_reason": "end_turn",
  "content": [
    {"type": "text", "text": "根据项目操作手册，运行提取任务的步骤如下...\n1. 首先确认 md/ 目录下有待处理的论文...\n2. 执行命令: bash scripts/run.sh ..."}
  ]
}
```

---

## 五、messages 数据结构演变

理解 `messages` 列表在整个过程中的变化，是理解这个脚本的关键：

```python
# 初始状态
messages = []

# 用户输入后
messages = [
    {"role": "user", "content": "帮我运行提取任务"}
]

# 第一轮 API 调用后（模型要调用工具）
messages = [
    {"role": "user", "content": "帮我运行提取任务"},
    {"role": "assistant", "content": [TextBlock(...), ToolUseBlock(...)]},
]

# 工具执行结果加入后
messages = [
    {"role": "user", "content": "帮我运行提取任务"},
    {"role": "assistant", "content": [TextBlock(...), ToolUseBlock(...)]},
    {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "...", "content": "SKILL.md内容..."}]},
]

# 第二轮 API 调用后（模型最终回答）
messages = [
    {"role": "user", "content": "帮我运行提取任务"},
    {"role": "assistant", "content": [TextBlock(...), ToolUseBlock(...)]},
    {"role": "user", "content": [{"type": "tool_result", ...}]},
    {"role": "assistant", "content": [TextBlock("根据项目操作手册...")]},
]
```

注意 role 始终保持 **user → assistant → user → assistant** 的交替模式。

---

## 六、核心概念总结

### 6.1 渐进式披露的三层对应

| 层级 | 理论概念 | 本脚本中的实现 |
|------|---------|---------------|
| 第一层：元数据 | 只加载 name + description | `load_skill_list()` 解析 frontmatter |
| 第二层：完整指令 | 按需加载 SKILL.md 全文 | 模型调用 `read_file` 工具读取 |
| 第三层：附加资源 | 按需加载脚本、数据文件 | 本示例未实现，但可扩展 |

### 6.2 Tool Use 协议的三个角色

```
Claude API（模型）  ◄──►  本脚本（客户端）  ◄──►  本地文件系统
     │                        │                      │
     │  tool_use 请求         │  handle_tool_call()   │  read file
     │ ──────────────►        │ ──────────────────►   │
     │                        │                      │
     │  tool_result 返回      │  文件内容返回          │
     │ ◄──────────────        │ ◄──────────────────   │
```

### 6.3 与 Cline/Claude Desktop 的对比

这个脚本本质上是 Cline 等 AI 编码工具的**极简版本**：

| 特性 | 本脚本 | Cline / Claude Desktop |
|------|--------|----------------------|
| 技能发现 | 扫描 `skills/` 目录 | 同样扫描 `skills/` 或 `.cline/skills/` |
| 元数据加载 | 解析 YAML frontmatter | 同样解析 frontmatter |
| 按需读取 | `read_file` 工具 | 内置的 `read_file` 工具 |
| 工具数量 | 只有 1 个 | 数十个（read_file, write_to_file, execute_command 等） |
| 交互方式 | 命令行 | IDE 集成 |

---

## 七、可扩展方向

基于这个最小示例，可以进行以下扩展：

1. **增加更多工具**：如 `execute_command`（执行 shell 命令）、`write_file`（写入文件）、`search_files`（搜索文件），使智能体具备更强的操作能力。

2. **实现第三层披露**：在 SKILL.md 中引用附加脚本（如 `check_extraction.py`），模型在需要时再读取和执行。

3. **对接 MCP 服务器**：将 `read_file` 替换为 MCP 标准协议的工具调用，实现更标准化的连接。

4. **添加对话持久化**：将 `messages` 保存到文件或数据库，支持跨会话的对话续接。

5. **多模型支持**：将 `anthropic.Anthropic()` 抽象为通用接口，支持 OpenAI、Gemini 等其他模型。
