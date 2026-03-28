"""
最简单的 skill agent 示例
运行: python agent.py
需要: pip install anthropic
"""
import os
import yaml
import anthropic

# ===== 第一步：扫描 skills 文件夹，提取 name + description =====
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


# ===== 第二步：把 skill 列表拼进 system prompt =====
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


# ===== 第三步：定义一个工具，让模型能读取文件 =====
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


# ===== 主循环 =====
def main():
    client = anthropic.Anthropic()  # 需要设置 ANTHROPIC_API_KEY 环境变量

    skills = load_skill_list("skills")
    system_prompt = build_system_prompt(skills)

    print("=== System Prompt ===")
    print(system_prompt)
    print("=====================\n")

    messages = []

    while True:
        user_input = input("你: ")
        if user_input.lower() in ("quit", "exit"):
            break

        messages.append({"role": "user", "content": user_input})

        # 调用模型
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        # 如果模型想调用工具（读取 SKILL.md），就执行后继续
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

        # 输出最终回复
        final_text = "".join(
            block.text for block in response.content if block.type == "text"
        )
        messages.append({"role": "assistant", "content": response.content})
        print(f"AI: {final_text}\n")


if __name__ == "__main__":
    main()

'''
一个技能就是一个构造指令包，通常包含：

my-skill/
├── SKILL.md          # 核心：触发条件 + 执行指令
├── scripts/          # 可选：可执行的脚本
├── references/       # 可选：补充文档
└── assets/           # 可选：模板、字体等资源
其中SKILL.md有关键部分：YAML前置两个元数据（名称+描述）和Markdown正文（具体指令）。

2.让Agent支持技能的核心架构
你需要实现三个模块：

①技能注册与发现——扫描技能目录，提取每个技能的name和description，形成一个简单的技能列表注入到Agent的系统提示中。这部分要保留产品，大约每个技能只放100词左右的描述。

②技能路由（触发判断） ——当用户发出来请求时，Agent根据技能列表中的描述判断是否需要调用某个技能。判断逻辑可以是LLM自身推理（像Claude这样直接在提示里列出available_skills让模型自己选），也可以用嵌入相似度匹配做预筛选。

③ 渐进式加载（Progressive Disclosure） — 关键设计。分三层加载：

第一层：始终位于上下文中的元数据（名称+描述），用于触发判断
第二层：触发后才读取的SKILL.md正文，包含详细指令
第三层：继续读取参考文档、脚本等资源

这样做的好处是不会让大量技能内容撑爆上下文窗口。

以写入为例：
{
    "name": "write_file",
    "description": "向指定路径写入或覆盖代码文件",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件保存路径"},
            "content": {"type": "string", "description": "要写入的完整代码内容"}
        },
        "required": ["path", "content"],
    },
}
第一步：在 TOOLS 列表中添加定义
Python

{
    "name": "write_file",
    "description": "向指定路径写入或覆盖代码文件",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件保存路径"},
            "content": {"type": "string", "description": "要写入的完整代码内容"}
        },
        "required": ["path", "content"],
    },
}

第二步：在 handle_tool_call 中实现物理写入
Python

def handle_tool_call(tool_name: str, tool_input: dict) -> str:
    # ... 读取逻辑 ...
    
    if tool_name == "write_file":
        path = tool_input["path"]
        code_content = tool_input["content"]
        
        # 安全检查：防止 AI 写到系统关键目录
        if ".." in path or path.startswith("/etc"):
            return "错误：禁止访问敏感目录！"

        try:
            # 真正的物理操作：Python 原生的文件写入
            with open(path, "w", encoding="utf-8") as f:
                f.write(code_content)
            return f"成功：已将代码写入到 {path}"
        except Exception as e:
            return f"写入失败：{str(e)}"
'''
