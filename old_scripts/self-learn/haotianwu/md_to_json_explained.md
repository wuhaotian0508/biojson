# md_to_json.py 工作原理详解

逐函数拆解 `scripts/md_to_json.py` 中的高级语法，并模拟调用。

## 流水线位置

```
md/ 目录下的 .md 文件
       │
       ▼
  md_to_json.py        ← 本文件
  ┌─────────────────────────────────────┐
  │ 1. stem_to_dirname()  文件名 → 目录名  │
  │ 2. Schema → EXTRACT_TOOL  构建 tool │
  │ 3. resolve_test_files() 测试筛选    │
  │ 4. ai_response()      核心提取逻辑   │
  │ 5. _fallback_extract_json() 回退    │
  │ 6. __main__ 块        入口调度       │
  └─────────────────────────────────────┘
       │
       ▼
  reports/{paper-dir}/extraction.json
```

---

## 目录

| # | 函数 | 核心语法 |
|---|------|----------|
| 1 | `stem_to_dirname()` | `str.startswith()`, `len()` 切片, `str.replace()` 链式调用 |
| 2 | Schema → EXTRACT_TOOL | `.get()` 链式取值, `.items()` 遍历, 动态构建嵌套 dict |
| 3 | `resolve_test_files()` | `str.isdigit()`, `str.endswith()`, `in` 模糊匹配 |
| 4 | `ai_response()` | `os.path` 三件套, truthy/falsy 短路求值, `isinstance()` 防御编程, f-string `:,` |
| 5 | `_fallback_extract_json()` | `re.search()` + `re.DOTALL`, `(.*?)` 非贪婪, `.group()`, 三元表达式 |
| 6 | `__main__` 块 | `if __name__`, `os.getenv()`, 模块级变量 |

---

## 1. `stem_to_dirname()` — 文件名标准化

将 MD 文件名 stem 转为 reports 子目录名（GitHub 命名规范）。

### 源码

```python
def stem_to_dirname(stem):
    if stem.startswith("MinerU_markdown_"):
        stem = stem[len("MinerU_markdown_"):]  # 切掉前缀
    stem = stem.replace("_(1)", "")             # 去掉括号
    stem = stem.replace("_", "-")               # 下划线转连字符
    return stem
```

### 语法讲解

#### `str.startswith()` — 判断前缀

```python
name = "MinerU_markdown_mmc3_2031567019886178304"
name.startswith("MinerU_markdown_")  # True
"new".startswith("MinerU_markdown_")  # False
```

#### `len()` 切片 — 去掉已知长度的前缀

```python
prefix = "MinerU_markdown_"
len(prefix)  # 16
name[16:]    # 'mmc3_2031567019886178304'

# 等价写法（Python 3.9+）：
name.removeprefix(prefix)  # 'mmc3_2031567019886178304'
```

关键思路：**已知前缀长度 → `name[len(prefix):]` 就是去掉前缀后的部分。**

#### `str.replace()` 链式调用 — 每次返回新字符串

```python
raw = "s41586-022-04950-4_(1)"
raw.replace("_(1)", "").replace("_", "-")
# → 's41586-022-04950-4'
```

`str.replace()` 不修改原字符串（字符串不可变），返回新字符串，所以可以连续 `.replace()`。

### 模拟调用

```python
stem_to_dirname("MinerU_markdown_mmc3_2031567019886178304")
# → 'mmc3-2031567019886178304'

stem_to_dirname("MinerU_markdown_s41586-022-04950-4_(1)_2031567254796566528")
# → 's41586-022-04950-4-2031567254796566528'

stem_to_dirname("new")
# → 'new'  （没有前缀，原样返回）
```

---

## 2. Schema → EXTRACT_TOOL — 动态构建 Function Calling 定义

从 JSON Schema 文件动态构建 OpenAI function_calling 的 tool 定义。

### 源码

```python
# 从 $defs 中取出基因字段定义
gene_def = paradigm.get("$defs", {}).get("NutrientMetabolismGene", {})

# 遍历每个字段，构建 GENE_PROPERTIES
for field_name, field_schema in gene_def.get("properties", {}).items():
    desc = field_schema.get("description", "")
    if field_name in ["Key_Intermediate_Metabolites_Affected", "Interacting_Proteins"]:
        GENE_PROPERTIES[field_name] = {"type": "array", "items": {"type": "string"}, ...}
    else:
        GENE_PROPERTIES[field_name] = {"type": "string", ...}
```

### 语法讲解

#### `.get()` 链式取值 — 安全访问嵌套字典

```python
data = {"a": {"b": {"c": 42}}}

# 安全取值：不存在时返回默认值 {}，不会报错
data.get("a", {}).get("b", {}).get("c", 0)  # 42
data.get("x", {}).get("y", {}).get("z", 0)  # 0

# 对比直接取值：不存在会 KeyError
data["x"]["y"]  # → KeyError!
```

关键思路：**`.get(key, {})` 的 default 是空字典 `{}`，这样即使 key 不存在，后续的 `.get()` 也不会报错。**

#### `.items()` 遍历字典 — 同时拿到 key 和 value

```python
schema_fields = {
    "Gene_Name": {"description": "基因名称"},
    "EC_Number": {"description": "EC 编号"},
}
for field_name, field_schema in schema_fields.items():
    print(f"{field_name}: {field_schema['description']}")
# Gene_Name: 基因名称
# EC_Number: EC 编号
```

### 模拟调用

```python
# 输入 schema（精简版）
mock_schema = {
    "$defs": {
        "NutrientMetabolismGene": {
            "properties": {
                "Gene_Name":    {"description": "Official gene symbol"},
                "Species":      {"description": "Species name"},
                "Key_Intermediate_Metabolites_Affected": {"description": "List of metabolites"},
            }
        }
    }
}

# 构建结果：
# Gene_Name                              → type=string
# Species                                → type=string
# Key_Intermediate_Metabolites_Affected  → type=array   ← 特殊处理
```

---

## 3. `resolve_test_files()` — 测试模式文件筛选

支持三种匹配方式：编号、精确文件名、模糊关键词。

### 源码

```python
def resolve_test_files(files):
    test_index = os.getenv("TEST_INDEX", "1")

    # 纯数字 → 按编号
    if test_index.isdigit():
        idx = int(test_index) - 1
        return [files[idx]]

    # 非数字 → 按文件名匹配
    target = test_index if test_index.endswith(".md") else test_index + ".md"
    matched = [f for f in files if f == target]       # 精确
    matched = [f for f in files if test_index in f]   # 模糊
```

### 语法讲解

#### `str.isdigit()` — 判断是否全为数字

```python
"3".isdigit()    # True
"42".isdigit()   # True
"new".isdigit()  # False
"3a".isdigit()   # False
"".isdigit()     # False
```

#### 三元表达式 — `A if 条件 else B`

```python
fname = "new"
target = fname if fname.endswith(".md") else fname + ".md"
# → "new.md"  （自动补上 .md）

fname = "new.md"
target = fname if fname.endswith(".md") else fname + ".md"
# → "new.md"  （已有 .md，不重复加）
```

#### `in` 运算符 — 子字符串检查 + 列表推导模糊匹配

```python
# 字符串中的 in：检查子串
"mmc3" in "MinerU_markdown_mmc3_2031567019886178304.md"  # True
"xyz"  in "MinerU_markdown_mmc3_2031567019886178304.md"  # False

# 列表推导中的 in：模糊匹配
files = ["aaa_mmc3_bbb.md", "ccc_mmc10_ddd.md", "new.md"]
[f for f in files if "mmc3" in f]  # ['aaa_mmc3_bbb.md']
```

### 模拟调用

```python
files = [
    "MinerU_markdown_mmc3_2031567019886178304.md",
    "MinerU_markdown_mmc10_2031567061837611008.md",
    "new.md",
]

TEST_INDEX="2"    → 🧪 按编号: 第 2 个 → MinerU_markdown_mmc10_...md
TEST_INDEX="new"  → 🧪 精确匹配 → new.md（自动补了 .md）
TEST_INDEX="mmc3" → 🧪 模糊匹配 → MinerU_markdown_mmc3_...md
TEST_INDEX="xyz"  → ❌ 未找到
```

---

## 4. `ai_response()` — 核心提取逻辑

这是最长的函数，包含路径处理、增量跳过、文本预处理、API 调用、空响应检测、JSON 解析、错误记录。

### 4.1 路径处理三件套

```python
name = os.path.basename(path)          # 取文件名
filename = os.path.splitext(name)[0]   # 去掉扩展名
paper_dir = os.path.join(REPORTS_DIR, stem_to_dirname(filename))
```

#### 模拟调用

```python
path = "/data/haotianwu/biojson/md/MinerU_markdown_mmc3_2031567019886178304.md"

os.path.basename(path)     # → 'MinerU_markdown_mmc3_2031567019886178304.md'
os.path.splitext(name)     # → ('MinerU_markdown_mmc3_2031567019886178304', '.md')
os.path.splitext(name)[0]  # → 'MinerU_markdown_mmc3_2031567019886178304'
stem_to_dirname(filename)  # → 'mmc3-2031567019886178304'
os.path.join(REPORTS_DIR, dirname)  # → '.../reports/mmc3-2031567019886178304'
```

### 4.2 Truthy/Falsy + 短路求值（空响应检测）

```python
has_tool_calls = message.tool_calls and len(message.tool_calls) > 0
has_content = message.content and message.content.strip()
if not has_tool_calls and not has_content:
    # API 返回了空内容 → 记录错误并跳过
```

#### Truthy / Falsy 速查

| 值 | `bool()` |
|----|----------|
| `None` | `False` |
| `""` | `False` |
| `"   "` | `True` ← 注意！空格字符串是 truthy |
| `[]` | `False` |
| `[1]` | `True` |
| `0` | `False` |

#### 短路求值 — `A and B`

A 为 falsy 时**直接返回 A**，不执行 B：

```python
content = None
content and content.strip()  # → None（不会报 AttributeError！短路了）

content = "  hello  "
content and content.strip()  # → 'hello'（content 有值，继续执行 .strip()）

content = "   "
content and content.strip()  # → ''（strip 后为空串，是 falsy）
```

#### 模拟调用

```
有 tool_calls        → ✅ 正常
有 content           → ✅ 正常
全 None              → ⚠️ 空响应
空列表+空字符串       → ⚠️ 空响应
None+纯空格          → ⚠️ 空响应
```

### 4.3 `isinstance()` 防御编程 — Genes 字符串自动修复

LLM 偶发把 Genes 数组序列化为字符串，需要检测并自动修复：

```python
if isinstance(json_data.get("Genes"), str):
    try:
        json_data["Genes"] = json.loads(json_data["Genes"])
    except json.JSONDecodeError:
        print("无法自动修复")
```

#### `isinstance()` — 安全类型检查

```python
isinstance([1, 2], list)   # True
isinstance('[1,2]', str)   # True
isinstance(None, str)      # False
```

#### 模拟调用

```python
# 场景1: 正常
data = {"Genes": [{"Gene_Name": "ZmPSY1"}]}
isinstance(data["Genes"], str)  # False → 不需要修复 ✅

# 场景2: LLM 返回了字符串
data = {"Genes": '[{"Gene_Name": "SlMYB12"}]'}
isinstance(data["Genes"], str)  # True → 修复!
json.loads(data["Genes"])  # → [{"Gene_Name": "SlMYB12"}]  🔧

# 场景3: 截断的字符串
data = {"Genes": '[{"Gene_Name": "OsMYB110"'}
json.loads(data["Genes"])  # → JSONDecodeError ⚠️ 无法修复
```

### 4.4 f-string `:,` 千分位格式化

```python
num = 45678
f"{num:,}"   # → '45,678'

# 源码中的用法：
f"文本预处理: {original_len:,} → {len(content):,} 字符"
# → '文本预处理: 45,678 → 40,678 字符'
```

---

## 5. `_fallback_extract_json()` — 正则回退解析

当 function_calling 未触发时，从 LLM 返回的纯文本中提取 JSON。三级回退策略。

### 源码

```python
def _fallback_extract_json(raw_result, name):
    # 优先: XML 标签
    tag_match = re.search(r'<structured_information>(.*?)</structured_information>',
                          raw_result, re.DOTALL)
    # 备选1: Markdown 代码块
    code_match = re.search(r'```json\s*(.*?)\s*```', raw_result, re.DOTALL)
    # 备选2: 花括号强力提取
    brace_match = re.search(r'(\{.*\})', raw_result, re.DOTALL)
    clean_json = brace_match.group(1).strip() if brace_match else raw_result
```

### 语法讲解

#### `re.DOTALL` — 让 `.` 匹配换行符

```python
text = "line1\nline2\nline3"

re.search(r"line1(.*)line3", text)             # → None（. 不匹配 \n）
re.search(r"line1(.*)line3", text, re.DOTALL)  # → 匹配成功！
```

默认情况 `.` 匹配除换行符外的任意字符。加 `re.DOTALL` 后 `.` 也能匹配 `\n`，适合跨行匹配。

#### `(.*?)` 非贪婪 vs `(.*)` 贪婪

```python
text = "<a>hello</a><a>world</a>"

re.search(r"<a>(.*)</a>", text).group(1)
# → 'hello</a><a>world'  ← 贪婪：尽量多匹配

re.search(r"<a>(.*?)</a>", text).group(1)
# → 'hello'              ← 非贪婪：尽量少匹配
```

#### `.group(n)` — 提取正则捕获组

```python
m = re.search(r"(\w+)@(\w+)\.(\w+)", "user@example.com")
m.group(0)  # 'user@example.com'  ← 整个匹配
m.group(1)  # 'user'              ← 第1个括号
m.group(2)  # 'example'           ← 第2个括号
m.group(3)  # 'com'               ← 第3个括号
```

#### 三元表达式 — `A if condition else B`

```python
# 源码中的用法：
clean_json = brace_match.group(1).strip() if brace_match else raw_result
# 如果匹配成功 → 取 group(1) 并 strip
# 如果匹配失败 → 用原始文本
```

### 模拟调用

```python
# 场景1: XML 标签包裹
raw = 'Result:\n<structured_information>{"Gene": "ZmPSY1"}</structured_information>'
# → 方式1 提取: {"Gene": "ZmPSY1"}

# 场景2: Markdown 代码块
raw = 'I found:\n```json\n{"Gene": "SlMYB12"}\n```'
# → 方式2 提取: {"Gene": "SlMYB12"}

# 场景3: 裸 JSON
raw = 'Some text {"Gene": "OsMYB55"} more text'
# → 方式3 提取: {"Gene": "OsMYB55"}
```

---

## 6. `__main__` 块 — 脚本入口

### 源码

```python
if __name__ == "__main__":
    files = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith('.md')])
    if os.getenv("TEST_MODE") == "1":
        files = resolve_test_files(files)
    for file in files:
        ai_response(os.path.join(INPUT_DIR, file))
    tracker.print_summary()
    if failed_files:
        print(f"⚠️  以下 {len(failed_files)} 个文件需要重跑:")
```

### 语法讲解

#### `if __name__ == "__main__"` — 脚本 vs 模块

```python
# 直接运行: python md_to_json.py
# → __name__ == "__main__"  → 执行

# 被导入: from md_to_json import stem_to_dirname
# → __name__ == "md_to_json"  → 不执行
```

#### `os.getenv()` — 读取环境变量

```python
os.getenv("HOME")                   # '/home/ubuntu'
os.getenv("NOT_EXIST")              # None
os.getenv("NOT_EXIST", "fallback")  # 'fallback'（提供默认值）
```

#### 模块级变量 — 跨函数共享状态

```python
# 模块顶层定义
failed_files = []

# ai_response() 函数内：
failed_files.append(name)  # ← 直接修改，不需要 global

# __main__ 块最后：
if failed_files:
    print(f"以下 {len(failed_files)} 个文件需要重跑")
```

**为什么不需要 `global`？** 因为 `.append()` 是修改列表对象本身（mutation），不是重新赋值。只有 `failed_files = [...]` 这种重新赋值才需要 `global`。

---

## 关键知识点总结

| 语法 | 所在函数 | 说明 |
|------|----------|------|
| `str.startswith()` | `stem_to_dirname` | 判断字符串前缀 |
| `len()` 切片 | `stem_to_dirname` | 去除已知长度的前缀 |
| `str.replace()` 链式 | `stem_to_dirname` | 连续替换，每次返回新字符串 |
| `.get()` 链式 | Schema 构建 | 安全访问嵌套字典，避免 KeyError |
| `.items()` | Schema 构建 | 同时遍历字典的 key 和 value |
| `str.isdigit()` | `resolve_test_files` | 判断字符串是否全为数字 |
| `str.endswith()` | `resolve_test_files` | 判断后缀，自动补 .md |
| `in` 运算符 | `resolve_test_files` | 子字符串检查 + 模糊匹配 |
| `os.path` 三件套 | `ai_response` | `basename` / `splitext` / `join` |
| Truthy/Falsy | `ai_response` | 空响应检测，短路求值 `and`/`or` |
| `isinstance()` | `ai_response` | 类型检查 + 防御性编程 |
| f-string `:,` | `ai_response` | 千分位数字格式化 |
| `re.search` + `DOTALL` | `_fallback_extract` | 跨行正则匹配 |
| `(.*?)` 非贪婪 | `_fallback_extract` | 最小匹配 vs 贪婪匹配 |
| `.group(n)` | `_fallback_extract` | 提取正则捕获组 |
| 三元表达式 | `_fallback_extract` | `A if cond else B` 单行写法 |
| `if __name__` | `__main__` | 脚本 vs 模块的入口控制 |
| `os.getenv()` | `__main__` | 读取环境变量 + 默认值 |
| 模块级变量 | `__main__` | `.append()` 跨函数共享，无需 `global` |
