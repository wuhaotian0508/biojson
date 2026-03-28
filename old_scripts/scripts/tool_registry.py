"""
tool_registry.py — Tool 注册中心 + 硬编码 tool call

学习自 agent-skills-demo.py 的三层架构：
  1. SKILL.md YAML 前置定义 tools（name, description, handler, schema_ref）
  2. ToolRegistry 注册 tools + handler
  3. call_tool() 单次强制调用指定 tool

对外暴露:
    ToolRegistry        — 核心类
    load_skill()        — 从 SKILL.md 加载技能并注册 tools
    load_skill_list()   — 扫描 skills 目录列出所有技能
"""

import json
import os
import re
import importlib
import yaml


class ToolCallResult:
    """单次 tool call 的结果。"""
    def __init__(self, tool_name, arguments, handler_result):
        self.tool_name = tool_name
        self.arguments = arguments
        self.handler_result = handler_result


class ToolRegistry:
    """Tool 注册中心 + 硬编码 tool call。

    用法:
        registry = ToolRegistry()
        registry.register("classify_genes", schema_dict, handler_func)

        # 硬编码调用：代码指定每步调哪个 tool
        result = registry.call_tool(client, model, messages, "classify_genes")
        result = registry.call_tools(client, model, messages, ["extract_pathway_genes", "extract_regulation_genes"])
    """

    def __init__(self):
        self._tools = {}       # name -> {"schema": dict, "handler": callable}
        self._call_log = []    # 所有 tool call 结果
        self._state = {}       # 共享状态，handlers 可以读写

    @property
    def state(self):
        return self._state

    @property
    def call_log(self):
        return self._call_log

    def register(self, name, schema, handler):
        """注册一个 tool。

        Args:
            name: tool 名称（须与 schema 中的 function.name 一致）
            schema: OpenAI function calling 格式的 tool 定义 dict
            handler: callable(arguments_dict, state_dict) -> str
                     接收 LLM 传来的参数和共享 state，返回 tool_result 字符串
        """
        self._tools[name] = {"schema": schema, "handler": handler}

    def get_openai_tools(self):
        """返回所有注册 tool 的 OpenAI 格式列表。"""
        return [t["schema"] for t in self._tools.values()]

    def handle(self, tool_name, arguments_json):
        """执行已注册的 tool handler。

        Args:
            tool_name: tool 名称
            arguments_json: LLM 返回的 JSON 字符串

        Returns:
            tool_result 字符串
        """
        if tool_name not in self._tools:
            return f"Error: unknown tool '{tool_name}'"

        # 安全解析 JSON
        args = self._safe_parse_json(arguments_json, tool_name)
        if args is None:
            return f"Error: failed to parse arguments for '{tool_name}'"

        handler = self._tools[tool_name]["handler"]
        result_str = handler(args, self._state)

        self._call_log.append(ToolCallResult(tool_name, args, result_str))
        return result_str

    def run_loop(self, client, model, messages, tracker=None, stage="extract",
                 file_name="", max_rounds=5, **api_kwargs):
        """核心：自动 tool call 循环。

        1. 调 API（带所有注册的 tools）
        2. 如果 LLM 返回 tool_calls → 本地 handle → 送回 messages
        3. 再次调 API → 重复直到 LLM 不再调用 tool 或达到 max_rounds

        Args:
            client: OpenAI 兼容客户端
            model: 模型名称
            messages: 初始消息列表（会被修改）
            tracker: TokenTracker 实例（可选）
            stage: tracker 用的阶段名
            file_name: tracker 用的文件名
            max_rounds: 最大循环轮数（防止无限循环）
            **api_kwargs: 传给 chat.completions.create 的额外参数

        Returns:
            (state_dict, call_log, success)
        """
        self._call_log = []
        tools = self.get_openai_tools()
        round_num = 0

        while round_num < max_rounds:
            round_num += 1

            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    **api_kwargs,
                )
            except Exception as e:
                print(f"    ❌ [{model}] API 错误 (第{round_num}轮): {e}")
                return self._state, self._call_log, False

            if tracker:
                tracker.add(response, stage=stage, file=file_name)

            message = response.choices[0].message

            # 检查是否有 tool calls
            if not message.tool_calls or len(message.tool_calls) == 0:
                # LLM 不再调用 tool → 循环结束
                if round_num == 1:
                    print(f"    ⚠️  [{model}] 第1轮就没有 tool call")
                    return self._state, self._call_log, len(self._call_log) > 0
                else:
                    print(f"    ✅ [{model}] 第{round_num}轮完成，LLM 不再调用 tool")
                    break

            # 把 assistant 消息加入历史
            messages.append(self._message_to_dict(message))

            # 处理每个 tool call
            tool_results = []
            for tc in message.tool_calls:
                fn_name = tc.function.name
                print(f"    🔧 [{model}] 第{round_num}轮 → {fn_name}")
                result_str = self.handle(fn_name, tc.function.arguments)
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_str,
                })

            # 把 tool results 加入历史
            messages.extend(tool_results)

        success = len(self._call_log) > 0
        return self._state, self._call_log, success

    # ── 硬编码 tool call 方法 ────────────────────────────────────────────────────

    def call_tool(self, client, model, messages, tool_name, *,
                  tracker=None, stage="extract", file_name="", **api_kwargs):
        """单次 API 调用，强制调用指定的 tool。

        代码硬编码控制调用哪个 tool，不让 LLM 自由选择。

        Args:
            client: OpenAI 兼容客户端
            model: 模型名称
            messages: 消息列表（会被修改，追加 assistant + tool 消息）
            tool_name: 强制调用的 tool 名称
            tracker: TokenTracker 实例（可选）
            stage: tracker 用的阶段名
            file_name: tracker 用的文件名
            **api_kwargs: 传给 API 的额外参数

        Returns:
            (parsed_args_dict, success)
            parsed_args_dict: LLM 返回的参数（已解析为 dict）
            success: 是否成功
        """
        if tool_name not in self._tools:
            print(f"    ❌ 未注册的 tool: {tool_name}")
            return None, False

        tool_schema = self._tools[tool_name]["schema"]

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=[tool_schema],
                tool_choice={"type": "function", "function": {"name": tool_name}},
                **api_kwargs,
            )
        except Exception as e:
            print(f"    ❌ [{model}] API 错误 (call_tool {tool_name}): {e}")
            return None, False

        if tracker:
            tracker.add(response, stage=stage, file=file_name)

        message = response.choices[0].message

        if not message.tool_calls or len(message.tool_calls) == 0:
            print(f"    ⚠️  [{model}] call_tool({tool_name}) 未触发 tool call")
            return None, False

        tc = message.tool_calls[0]
        fn_name = tc.function.name
        print(f"    🔧 [{model}] → {fn_name}")

        # 执行 handler
        result_str = self.handle(fn_name, tc.function.arguments)

        # 追加到 messages 历史（保持对话连贯）
        messages.append(self._message_to_dict(message))
        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": result_str,
        })

        # 返回解析后的参数
        parsed_args = self._safe_parse_json(tc.function.arguments, tool_name)
        return parsed_args, True

    def call_tools(self, client, model, messages, tool_names, *,
                   tracker=None, stage="extract", file_name="", **api_kwargs):
        """单次 API 调用，提供多个 tool 让 LLM 并行调用。

        适用于：已知需要调用多个 extract tool（如 extract_pathway + extract_regulation），
        一次 API 调用让 LLM 并行返回多个 tool call。

        Args:
            client: OpenAI 兼容客户端
            model: 模型名称
            messages: 消息列表（会被修改）
            tool_names: 要提供的 tool 名称列表
            tracker: TokenTracker 实例（可选）
            stage: tracker 用的阶段名
            file_name: tracker 用的文件名
            **api_kwargs: 传给 API 的额外参数

        Returns:
            (results_dict, success)
            results_dict: {tool_name: parsed_args_dict} 每个被调用的 tool 的参数
            success: 是否至少有一个 tool 被成功调用
        """
        tool_schemas = []
        for name in tool_names:
            if name not in self._tools:
                print(f"    ⚠️  跳过未注册的 tool: {name}")
                continue
            tool_schemas.append(self._tools[name]["schema"])

        if not tool_schemas:
            return {}, False

        # 如果只有一个 tool，强制调用；多个则用 auto
        if len(tool_schemas) == 1:
            tc_choice = {"type": "function", "function": {"name": tool_names[0]}}
        else:
            tc_choice = "auto"

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tool_schemas,
                tool_choice=tc_choice,
                **api_kwargs,
            )
        except Exception as e:
            print(f"    ❌ [{model}] API 错误 (call_tools): {e}")
            return {}, False

        if tracker:
            tracker.add(response, stage=stage, file=file_name)

        message = response.choices[0].message

        if not message.tool_calls or len(message.tool_calls) == 0:
            print(f"    ⚠️  [{model}] call_tools({tool_names}) 未触发 tool call")
            return {}, False

        # 追加 assistant 消息
        messages.append(self._message_to_dict(message))

        # 处理每个 tool call
        results = {}
        for tc in message.tool_calls:
            fn_name = tc.function.name
            print(f"    🔧 [{model}] → {fn_name}")
            result_str = self.handle(fn_name, tc.function.arguments)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_str,
            })
            parsed = self._safe_parse_json(tc.function.arguments, fn_name)
            if parsed:
                results[fn_name] = parsed

        return results, len(results) > 0

    # ── 辅助方法 ──────────────────────────────────────────────────────────────────

    def _safe_parse_json(self, json_str, tool_name):
        """安全解析 JSON，支持截断修复。"""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # 尝试修复截断
        repaired = self._repair_truncated_json(json_str)
        if repaired is not None:
            print(f"    🔧 [{tool_name}] 截断 JSON 已自动修复")
            return repaired

        print(f"    ❌ [{tool_name}] JSON 无法解析也无法修复")
        return None

    @staticmethod
    def _repair_truncated_json(json_str):
        """尝试修复被截断的 JSON 字符串。"""
        last_brace = json_str.rfind('}')
        if last_brace == -1:
            return None

        truncated = json_str[:last_brace + 1]
        open_braces = truncated.count('{') - truncated.count('}')
        open_brackets = truncated.count('[') - truncated.count(']')
        repair = truncated + ']' * max(0, open_brackets) + '}' * max(0, open_braces)

        try:
            return json.loads(repair)
        except json.JSONDecodeError:
            # 更激进：找最后一个完整的 },
            endings = list(re.finditer(r'\}\s*,', json_str))
            if not endings:
                return None
            last_complete = endings[-1].end() - 1
            partial = json_str[:last_complete].rstrip(',').rstrip()
            ob = partial.count('{') - partial.count('}')
            repair2 = partial + '}' * max(0, ob)
            ob2 = repair2.count('[') - repair2.count(']')
            repair2 += ']' * max(0, ob2)
            ob3 = repair2.count('{') - repair2.count('}')
            repair2 += '}' * max(0, ob3)
            try:
                return json.loads(repair2)
            except json.JSONDecodeError:
                return None

    @staticmethod
    def _message_to_dict(message):
        """将 OpenAI message 对象转为 dict 格式（兼容不同 API provider）。"""
        msg = {"role": "assistant"}

        # 处理 content
        if message.content:
            msg["content"] = message.content
        else:
            msg["content"] = None

        # 处理 tool_calls
        if message.tool_calls:
            msg["tool_calls"] = []
            for tc in message.tool_calls:
                msg["tool_calls"].append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                })

        return msg


# ═══════════════════════════════════════════════════════════════════════════════════
#  从 SKILL.md 加载技能
# ═══════════════════════════════════════════════════════════════════════════════════

def load_skill_list(skills_dir):
    """扫描 skills 目录，返回所有技能的元数据列表。

    类似 agent-skills-demo.py 中的 load_skill_list()。
    """
    skills = []
    if not os.path.isdir(skills_dir):
        return skills

    for name in os.listdir(skills_dir):
        skill_path = os.path.join(skills_dir, name, "SKILL.md")
        if not os.path.isfile(skill_path):
            continue
        meta = _parse_skill_yaml(skill_path)
        if meta:
            meta["skill_dir"] = os.path.join(skills_dir, name)
            meta["skill_path"] = skill_path
            skills.append(meta)

    return skills


def load_skill(skill_dir, schema_base_dir=None):
    """从单个 skill 目录加载技能，返回 ToolRegistry 实例。

    读取 SKILL.md YAML 前置中的 tools 定义，动态导入 handler 并注册。

    Args:
        skill_dir: 技能目录路径（如 "skills/biojson-extraction"）
        schema_base_dir: schema 文件的基础目录（默认为项目根目录）

    Returns:
        ToolRegistry 实例（已注册所有 tools）
    """
    skill_path = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(skill_path):
        raise FileNotFoundError(f"SKILL.md not found: {skill_path}")

    meta = _parse_skill_yaml(skill_path)
    if not meta:
        raise ValueError(f"Failed to parse SKILL.md YAML: {skill_path}")

    if schema_base_dir is None:
        schema_base_dir = os.getenv("BASE_DIR", "/data/haotianwu/biojson")

    print(f"📦 加载技能: {meta.get('name', 'unknown')} v{meta.get('version', '?')}")
    print(f"   {meta.get('description', '')[:80]}")

    registry = ToolRegistry()
    tools_config = meta.get("tools", [])

    for tool_cfg in tools_config:
        tool_name = tool_cfg["name"]
        handler_ref = tool_cfg["handler"]  # e.g. "handlers.handle_classify"
        schema_ref = tool_cfg.get("schema_ref")  # e.g. "configs/nutri_gene_schema_v2.json#PathwayGeneExtraction"

        # 动态导入 handler
        handler = _import_handler(skill_dir, handler_ref)

        # 构建 OpenAI tool schema
        tool_schema = _build_tool_schema(tool_cfg, schema_ref, schema_base_dir)

        registry.register(tool_name, tool_schema, handler)
        print(f"   🔧 注册 tool: {tool_name}")

    print(f"   ✅ 共注册 {len(tools_config)} 个 tools")
    return registry


# ── 内部辅助 ──────────────────────────────────────────────────────────────────────

def _parse_skill_yaml(skill_path):
    """解析 SKILL.md 的 YAML 前置元数据。"""
    with open(skill_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 分割 YAML frontmatter
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None

    try:
        meta = yaml.safe_load(parts[1])
        return meta
    except yaml.YAMLError as e:
        print(f"  ⚠️  YAML 解析错误 {skill_path}: {e}")
        return None


def _import_handler(skill_dir, handler_ref):
    """动态导入 handler 函数。

    handler_ref 格式: "module_name.function_name"
    例如: "handlers.handle_classify" → 从 skill_dir/handlers.py 导入 handle_classify
    """
    parts = handler_ref.rsplit(".", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid handler ref: {handler_ref} (expected 'module.function')")

    module_name, func_name = parts

    # 构建模块文件路径
    module_path = os.path.join(skill_dir, f"{module_name}.py")
    if not os.path.isfile(module_path):
        raise FileNotFoundError(f"Handler module not found: {module_path}")

    # 动态导入
    spec = importlib.util.spec_from_file_location(
        f"skill_handler_{module_name}", module_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    handler = getattr(module, func_name, None)
    if handler is None:
        raise AttributeError(f"Handler function '{func_name}' not found in {module_path}")

    return handler


def _build_tool_schema(tool_cfg, schema_ref, schema_base_dir):
    """构建 OpenAI function calling 格式的 tool schema。

    如果 tool_cfg 中有 inline_parameters，直接使用；
    否则从 schema_ref 引用的 JSON 文件构建。
    """
    tool_name = tool_cfg["name"]
    description = tool_cfg.get("description", "")

    # 如果有内联参数定义
    if "parameters" in tool_cfg:
        return {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": description,
                "parameters": tool_cfg["parameters"],
            }
        }

    # 从 schema_ref 构建
    if schema_ref:
        file_path, fragment = schema_ref.split("#", 1) if "#" in schema_ref else (schema_ref, None)
        full_path = os.path.join(schema_base_dir, file_path)

        with open(full_path, "r", encoding="utf-8") as f:
            schema_data = json.load(f)

        if fragment:
            extraction_def = schema_data.get(fragment, {})
        else:
            extraction_def = schema_data

        # 从 $defs 中获取基因类型的 properties
        defs = extraction_def.get("$defs", {})
        # 取第一个 def（通常只有一个，如 CommonGene, PathwayGene 等）
        gene_type_name = list(defs.keys())[0] if defs else None
        gene_props = {}
        if gene_type_name:
            gene_def = defs[gene_type_name]
            gene_props = _schema_props_to_fc(gene_def)

        return {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "genes": {
                            "type": "array",
                            "description": f"Detailed information for each gene.",
                            "items": {"type": "object", "properties": gene_props}
                        }
                    },
                    "required": ["genes"]
                }
            }
        }

    # 最后回退：空参数
    return {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": description,
            "parameters": {"type": "object", "properties": {}}
        }
    }


def _schema_props_to_fc(gene_def):
    """将 schema JSON 中一个 Gene 类型的 properties 转为
    function calling 兼容格式（anyOf → string，保留 description）。"""
    fc_props = {}
    for field_name, field_schema in gene_def.get("properties", {}).items():
        desc = field_schema.get("description", "")
        fc_props[field_name] = {"type": "string", "description": desc}
    return fc_props
