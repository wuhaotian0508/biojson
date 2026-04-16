---
name: skill-creator
description: Create new skills or modify existing skills for this agent system. Use when the user wants to add a new skill, update a skill's instructions, or asks about skill structure and best practices.
tools: [execute_shell, read_tool, write_tool]
---

# Skill Creator

创建和管理 `skills/` 目录下的 skill。每个 skill 是一个包含 `skill.md` 的文件夹。

## Skill 结构

```
skills/
└── <skill-name>/
    ├── skill.md          # 必需：YAML frontmatter + Markdown 指令
    ├── scripts/          # 可选：可执行脚本
    └── references/       # 可选：参考文档（按需加载）
```

## skill.md 格式

```markdown
---
name: <skill-name>
description: <做什么> + <什么时候触发>
---

<Markdown 指令正文>
```

- **name**: 小写字母 + 连字符，简短动词短语（如 `code-review`、`deep-think`），必须与目录名一致
- **description**: 既说明功能，也说明触发条件。这是 agent 决定是否使用该 skill 的唯一依据

## 创建流程

### 1. 明确用途

向用户确认：
- 这个 skill 解决什么问题？
- 用户会怎样触发它？（给出示例 prompt）
- 需要什么样的输出？

### 2. 用脚本初始化

用 `execute_shell` 运行初始化脚本，自动生成 skill 目录和模板文件：

```bash
python skills/skill-creator/scripts/init_skill.py <skill-name> --path skills/
```

可选添加资源目录：

```bash
python skills/skill-creator/scripts/init_skill.py <skill-name> --path skills/ --resources scripts,references
```

脚本会自动：
- 规范化名称（大写→小写，空格→连字符）
- 创建目录结构
- 生成带 TODO 占位符的 skill.md 模板
- 按需创建 scripts/ 和 references/ 子目录

### 3. 编写 frontmatter

```yaml
---
name: my-skill
description: Do X for the user. Use when the user asks to Y or needs Z.
---
```

**description 原则**：
- 包含"Use when..."触发条件
- 覆盖所有触发场景
- 具体而非抽象
- 不含 TODO 占位符、不含尖括号、不超过 1024 字符

### 4. 编写正文

**原则**：
- 只写 agent 不知道的内容（agent 已经很聪明）
- 用祈使句（"分析问题" 而非 "你应该分析问题"）
- 简洁优先：每句话都要有信息量
- 步骤编号，便于 agent 跟踪执行进度
- 正文 < 200 行

**正文结构参考**：

```markdown
# Skill 标题

## 核心流程
1. 步骤一 — 做什么
2. 步骤二 — 做什么

## 关键规则
- 必须遵守的约束
- 输出格式要求
```

### 5. 验证

用 `execute_shell` 运行验证脚本，检查结构和 frontmatter 是否合法：

```bash
python skills/skill-creator/scripts/validate_skill.py skills/<skill-name>
```

验证项：
- skill.md 存在且 frontmatter 格式正确
- name 是合法的连字符格式且与目录名一致
- description 非空、无 TODO 占位符、不超长
- 目录中无多余文件（只允许 skill.md、scripts/、references/）

验证通过后告知用户 skill 已创建完毕。

## 示例

创建一个 `code-review` skill：

```markdown
---
name: code-review
description: Review code for bugs, style, and performance issues. Use when the user asks to review, check, or audit code quality.
---

# Code Review

## 流程
1. 用 read_tool 读取目标文件
2. 按以下维度逐项检查：
   - **正确性** — 逻辑错误、边界情况
   - **安全性** — 注入、泄露、权限问题
   - **性能** — 不必要的循环、重复计算
   - **可读性** — 命名、结构、注释
3. 输出结构化报告：问题 + 严重程度 + 修改建议
```
