# 🔧 Function Calling 机制详解 — md_to_json.py 中的 EXTRACT_TOOL

本文档解释 `md_to_json.py` 中 **构建 function_calling tool 定义** 那段代码是怎么运作的。

---

## 一、什么是 Function Calling？

普通的 LLM 调用：你发消息 → LLM 返回**自由文本**（可能格式乱七八糟）。

Function Calling：你告诉 LLM "我有一个函数，它的参数是这样的" → LLM 被**强制按你定义的参数格式**返回 JSON。

```
普通调用:   用户消息 → LLM → "这篇论文有3个基因..." (自由文本，需要正则提取)
Function:   用户消息 + 工具定义 → LLM → {"Title": "...", "Genes": [...]} (结构化 JSON)
```

**好处**：不需要写复杂的正则来解析 LLM 输出，100% 保证返回合法 JSON。

---

## 一·五、用最简单的例子直观理解（先忽略项目代码）

假设你想让 LLM 从一段文字中提取一个人的信息，只要 **姓名** 和 **年龄** 两个字段。

### 步骤 1：定义"工具"（其实就是定义你想要的 JSON 格式）

```python
my_tool = {
    "type": "function",
    "function": {
        "name": "extract_person",             # 随便起个名字
        "description": "从文字中提取人物信息",   # 告诉 LLM 这个函数干嘛
        "parameters": {
            "type": "object",                  # 返回一个 JSON 对象 {}
            "properties": {
                "name": {
                    "type": "string",
                    "description": "人物姓名"
                },
                "age": {
                    "type": "integer",
                    "description": "人物年龄"
                }
            },
            "required": ["name", "age"]
        }
    }
}
```

这个字典翻译成人话就是：

> "嘿 LLM，我有一个函数叫 `extract_person`，它需要两个参数：`name`（字符串）和 `age`（整数）。请你从用户给的文字里提取这两个信息，按这个格式返回给我。"

### 步骤 2：调用 API 时传入这个工具

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "张三今年25岁，是一名工程师。"}
    ],
    tools=[my_tool],                          # ← 把工具定义传进去
    tool_choice={"type": "function", "function": {"name": "extract_person"}}  # ← 强制使用
)
```

### 步骤 3：LLM 返回的结果

**如果不用 function calling**，LLM 可能返回：
```
"根据文本，张三的年龄是25岁。他是一名工程师。"   ← 自由文本，你还得自己解析
```

**用了 function calling**，LLM 返回的是：
```python
response.choices[0].message.tool_calls[0].function.arguments
# 结果是一个 JSON 字符串：
# '{"name": "张三", "age": 25}'
```

你直接 `json.loads()` 就能得到一个干干净净的 Python 字典：

```python
import json
data = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
print(data["name"])   # → 张三
print(data["age"])    # → 25
```

### 完整流程图

```
你定义的工具（模板）：                 LLM 返回的数据（填好的表格）：

{                                    {
  "name": (请填字符串),     →LLM→      "name": "张三",
  "age":  (请填整数)                    "age": 25
}                                    }
```

**本质就是：你给 LLM 一张空表格，LLM 帮你填好还回来。**

### 对比我们项目的 EXTRACT_TOOL

| 简单例子 | 我们的项目 |
|---------|-----------|
| 工具名：`extract_person` | 工具名：`extract_nutrient_genes` |
| 2 个字段：name, age | 4 + 42 = 46 个字段：Title, Journal, DOI, Genes (内含 42 个基因字段) |
| 平铺结构：`{name, age}` | 嵌套结构：`{Title, Journal, DOI, Genes: [{42个字段}, {42个字段}, ...]}` |
| 字段类型：string, integer | 字段类型：string, array |

**原理完全一样**，只是我们的"表格"更大、有嵌套（Genes 是一个数组，每个元素又是一个包含 42 个字段的对象）。

---

## 二、代码分两步

### 第 1 步：从 JSON Schema 文件动态构建字段定义

```python
# 读取 configs/nutri_plant.json
with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
    template = json.load(f)
    paradigm = template.get("CropNutrientMetabolismGeneExtraction", template)
```

`nutri_plant.json` 里定义了 42 个基因字段，每个字段长这样：

```json
"Gene_Name": {
    "anyOf": [{ "type": "string" }, { "type": "null" }],
    "default": "NA",
    "description": "Gene symbol/name used in the paper (e.g., OsNAS2, ZmPSY1)"
}
```

### 第 2 步：转换格式，因为 function_calling 不支持 `anyOf`

```python
GENE_PROPERTIES = {}
gene_def = paradigm.get("$defs", {}).get("NutrientMetabolismGene", {})

for field_name, field_schema in gene_def.get("properties", {}).items():
    desc = field_schema.get("description", "")
    
    # 特殊处理：这两个字段是数组类型
    if field_name == "Key_Intermediate_Metabolites_Affected" or field_name == "Interacting_Proteins":
        GENE_PROPERTIES[field_name] = {
            "type": "array",
            "items": {"type": "string"},
            "description": desc
        }
    else:
        # 其他所有字段统一简化为 string
        GENE_PROPERTIES[field_name] = {
            "type": "string",
            "description": desc
        }
```

#### 为什么要转换？

| nutri_plant.json 中的写法 | function_calling 需要的写法 | 原因 |
|---------------------------|---------------------------|------|
| `"anyOf": [{"type": "string"}, {"type": "null"}]` | `"type": "string"` | OpenAI function_calling 不认识 `anyOf` |
| `"type": "array", "items": {"type": "string"}` | 保持不变 | 数组类型是支持的 |

#### 转换前后对比：

```
转换前（nutri_plant.json）:
  "Gene_Name": {
      "anyOf": [{"type": "string"}, {"type": "null"}],   ← 不兼容
      "default": "NA",
      "description": "Gene symbol..."
  }

转换后（GENE_PROPERTIES）:
  "Gene_Name": {
      "type": "string",                                    ← 简化了
      "description": "Gene symbol..."
  }
```

---

## 三、组装完整的 EXTRACT_TOOL（逐层拆解）

EXTRACT_TOOL 是一个**多层嵌套的字典**，看起来很吓人，但每一层都有明确的含义。下面逐层剥开来看。

### 3.1 最外层：告诉 API "这是一个函数类型的工具"

```python
EXTRACT_TOOL = {
    "type": "function",   # ← 工具类型：函数
    "function": { ... }   # ← 函数的具体定义
}
```

OpenAI 的 `tools` 参数接受一个**工具列表**，每个工具必须声明自己的类型。目前唯一支持的类型就是 `"function"`（未来可能增加其他类型如 `"code_interpreter"` 等）。

**类比**：这层相当于一个信封，信封上写着"这是一份函数说明书"，具体内容在 `function` 里面。

---

### 3.2 `function` 层：函数的"身份证"

```python
"function": {
    "name": "extract_nutrient_genes",
    "description": "Extract crop nutrient metabolism gene information from a scientific paper. ...",
    "parameters": { ... }
}
```

| 键 | 含义 | 重要性 |
|---|---|---|
| `name` | 函数名称。LLM 返回时会在 `tool_calls[0].function.name` 里引用这个名字，告诉你它"调用了哪个函数" | 必须唯一，且是合法的函数名格式（字母/数字/下划线） |
| `description` | 告诉 LLM 这个函数**干什么用**。LLM 根据这段描述来决定是否调用这个函数、以及如何填充参数 | 写得越清楚，LLM 提取越准确 |
| `parameters` | 函数的**参数签名**——定义了 LLM 返回的 JSON 必须长什么样 | 核心部分，下面详细拆解 |

> ⚠️ 注意：这里的 "函数" 并不是真正的 Python 函数。你不需要真的定义一个叫 `extract_nutrient_genes()` 的函数。这只是一个**格式约束**——告诉 LLM "请按这个格式返回数据"。LLM 返回后，你自己拿到 JSON 数据随便处理。

---

### 3.3 `parameters` 层：定义 LLM 必须返回的 JSON 结构

```python
"parameters": {
    "type": "object",         # ← 顶层必须是一个 JSON 对象 {}
    "properties": { ... },    # ← 对象里有哪些键（字段）
    "required": ["Title", "Journal", "DOI", "Genes"]  # ← 哪些字段是必填的
}
```

这层遵循 **JSON Schema** 语法（和 `nutri_plant.json` 同一套标准，但只用了 function_calling 支持的子集）。

| 键 | 含义 |
|---|---|
| `"type": "object"` | LLM 返回的最外层必须是 `{ }`（JSON 对象），不能是数组或字符串 |
| `"properties"` | 定义这个对象里面**有哪些键**，以及每个键的**类型**和**描述** |
| `"required"` | 列出必填字段。LLM 会确保这些字段一定出现在返回的 JSON 中 |

**类比**：`parameters` 相当于定义了一张"表单"——有哪些字段、每个字段是什么类型、哪些必须填写。

---

### 3.4 `properties` 层：表单里的具体字段

```python
"properties": {
    "Title":   {"type": "string", "description": "Full paper title."},
    "Journal": {"type": "string", "description": "Journal name."},
    "DOI":     {"type": "string", "description": "Pure DOI string, no URL prefix."},
    "Genes":   { ... }    # ← 这个比较复杂，单独拆解
}
```

前三个字段很简单：

| 字段 | 类型 | LLM 看到的说明 | LLM 会返回的值（示例） |
|---|---|---|---|
| `Title` | `string` | "Full paper title." | `"Engineering carotenoid flux..."` |
| `Journal` | `string` | "Journal name." | `"Plant Biotechnology Journal"` |
| `DOI` | `string` | "Pure DOI string, no URL prefix." | `"10.1111/pbi.12345"` |

每个字段都是一个小字典，包含 `type`（类型）和 `description`（描述）。`description` 非常重要——**LLM 就是根据这段文字来理解每个字段应该填什么内容的**。

---

### 3.5 `Genes` 字段：嵌套结构的核心（重点！）

`Genes` 是最复杂的字段，因为它是一个**数组**，数组里每个元素是一个**包含 42 个字段的对象**。嵌套了 4 层：

```python
"Genes": {
    "type": "array",                    # 第 1 层：Genes 是一个数组 [...]
    "description": "List of key gene objects...",
    "items": {                           # 第 2 层：数组里每个元素长什么样？
        "type": "object",               # 第 3 层：每个元素是一个对象 {...}
        "properties": GENE_PROPERTIES   # 第 4 层：对象里有哪些字段？→ 42 个基因字段
    }
}
```

逐层解释：

```
"Genes": {
│
├── "type": "array"
│   └── 告诉 LLM：Genes 的值是一个数组 []
│       例如: "Genes": [ gene1, gene2, gene3 ]
│
├── "description": "List of key gene objects..."
│   └── 告诉 LLM：这个数组里放的是什么东西
│
└── "items": {                          ← 定义数组中每个元素的格式
        │
        ├── "type": "object"
        │   └── 每个元素是一个 JSON 对象 {}
        │
        └── "properties": GENE_PROPERTIES
            └── 这个对象里有 42 个字段（Gene_Name, Species, ...）
                这就是上一节用 for 循环动态构建的那个字典！
    }
```

**类比**：
- `Genes` 是一个"文件夹"（数组）
- 文件夹里装着多个"基因档案"（对象）
- 每个"基因档案"都有 42 个"表格字段"（properties）

LLM 最终返回的结构长这样：

```json
{
    "Title": "Engineering carotenoid flux...",
    "Journal": "Plant Biotechnology Journal",
    "DOI": "10.1111/pbi.12345",
    "Genes": [                          ← array
        {                               ← object (第 1 个基因)
            "Gene_Name": "ZmPSY1",      ← GENE_PROPERTIES 里的字段
            "Species": "Maize",
            "Final_Nutrient_Product": "β-carotene",
            "Key_Intermediate_Metabolites_Affected": ["phytoene", "lycopene"],
            ...共 42 个字段
        },
        {                               ← object (第 2 个基因)
            "Gene_Name": "ZmCRTISO",
            "Species": "Maize",
            ...
        }
    ]
}
```

---

### 3.6 `GENE_PROPERTIES` 的嵌入点

回顾一下 `GENE_PROPERTIES` 是怎么来的（第二节的代码）：

```python
GENE_PROPERTIES = {}
for field_name, field_schema in gene_def.get("properties", {}).items():
    desc = field_schema.get("description", "")
    if field_name in ("Key_Intermediate_Metabolites_Affected", "Interacting_Proteins"):
        GENE_PROPERTIES[field_name] = {"type": "array", "items": {"type": "string"}, "description": desc}
    else:
        GENE_PROPERTIES[field_name] = {"type": "string", "description": desc}
```

循环结束后，`GENE_PROPERTIES` 长这样（简化示意）：

```python
GENE_PROPERTIES = {
    "Gene_Name":             {"type": "string", "description": "Gene symbol/name..."},
    "Gene_Accession_Number": {"type": "string", "description": "Accession/ID..."},
    "Species":               {"type": "string", "description": "Crop species..."},
    ...                      # (共 40 个 string 字段)
    "Key_Intermediate_Metabolites_Affected": {"type": "array", "items": {"type": "string"}, "description": "..."},
    "Interacting_Proteins":                  {"type": "array", "items": {"type": "string"}, "description": "..."},
}
```

然后这个字典被**直接嵌入**到 EXTRACT_TOOL 的 `Genes → items → properties` 位置：

```python
"Genes": {
    "type": "array",
    "items": {
        "type": "object",
        "properties": GENE_PROPERTIES   # ← 就是上面那个字典，Python 直接引用
    }
}
```

> 💡 Python 的字典赋值是**引用传递**，所以 `GENE_PROPERTIES` 这个变量的值直接嵌入到了 EXTRACT_TOOL 字典中，不需要 copy，也不需要什么特殊操作。

---

### 3.7 `required` 字段：哪些必须填

```python
"required": ["Title", "Journal", "DOI", "Genes"]
```

这告诉 LLM：**这 4 个字段是必填的**，返回的 JSON 中一定要包含它们。

注意：`Genes` 数组内部的 42 个基因字段**没有设置 required**，意味着 LLM 可以按需填写。找不到的信息字段可以填 `"NA"` 或者省略。

---

### 3.8 完整结构树

把上面所有层放在一起，最终结构是这样的：

```
EXTRACT_TOOL                              ← 最外层字典
│
├── type: "function"                      ← 声明工具类型
│
└── function                              ← 函数定义
      │
      ├── name: "extract_nutrient_genes"  ← 函数名（LLM 返回时引用）
      │
      ├── description: "Extract crop..."  ← 函数用途（引导 LLM 行为）
      │
      └── parameters                      ← 参数签名（JSON Schema 格式）
            │
            ├── type: "object"            ← 返回值是一个 JSON 对象
            │
            ├── properties                ← 对象的字段定义
            │     │
            │     ├── Title (string)      ← 论文标题
            │     ├── Journal (string)    ← 期刊名
            │     ├── DOI (string)        ← DOI
            │     │
            │     └── Genes (array)       ← 基因列表
            │           │
            │           └── items (object)        ← 每个基因是一个对象
            │                 │
            │                 └── properties      ← GENE_PROPERTIES（42 个字段）
            │                       │
            │                       ├── Gene_Name (string)
            │                       ├── Gene_Accession_Number (string)
            │                       ├── Species (string)
            │                       ├── ... (共 40 个 string 字段)
            │                       ├── Key_Intermediate_Metabolites_Affected (array<string>)
            │                       └── Interacting_Proteins (array<string>)
            │
            └── required: [Title, Journal, DOI, Genes]   ← 必填字段
```

---

## 四、怎么使用这个 TOOL？

在 API 调用时传入：

```python
response = client.chat.completions.create(
    model="...",
    messages=[...],
    tools=[EXTRACT_TOOL],                                              # ← 传入工具定义
    tool_choice={"type": "function", "function": {"name": "extract_nutrient_genes"}},  # ← 强制调用
)
```

- `tools=[EXTRACT_TOOL]`：告诉 LLM "你可以调用这个函数"
- `tool_choice={"type": "function", ...}`：**强制** LLM 必须调用（不允许返回自由文本）

### LLM 返回的结果：

```python
message = response.choices[0].message

if message.tool_calls:
    tool_call = message.tool_calls[0]
    json_str = tool_call.function.arguments   # ← 这就是结构化的 JSON 字符串
    json_data = json.loads(json_str)           # ← 直接解析，不需要正则
```

---

## 五、数据流全景

```
configs/nutri_plant.json          ← 42 个字段的 Schema 定义（anyOf 格式）
        │
        ▼
for 循环转换为 GENE_PROPERTIES    ← 简化为 function_calling 兼容格式
        │
        ▼
组装 EXTRACT_TOOL                 ← 完整的 tool 定义（嵌套结构）
        │
        ▼
client.chat.completions.create(   ← API 调用时传入
    tools=[EXTRACT_TOOL],
    tool_choice=强制调用
)
        │
        ▼
response.tool_calls[0].function.arguments  ← LLM 返回的结构化 JSON
        │
        ▼
json.loads() → 保存为 _nutri_plant.json
```

---

## 六、如果 Function Calling 不触发怎么办？

有些 API 不支持 function_calling，这时候走 fallback：

```python
if message.tool_calls:
    # ✅ 正常路径：直接取 JSON
else:
    # ⚠️ Fallback：从自由文本中用正则提取 JSON
    raw_result = message.content
    json_data = _fallback_extract_json(raw_result, name)
```

Fallback 的提取顺序：
1. 找 `<structured_information>` 标签
2. 找 `` ```json ``` `` 代码块
3. 找第一个 `{` 到最后一个 `}`
