import json
import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from token_tracker import TokenTracker
from text_utils import preprocess_md
load_dotenv()

# 1. 初始化客户端
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")  # 确保加上了 /v1
)

# Fallback 客户端（DeepSeek）：当主 API 因危险词被拦截时自动切换
fallback_client = None
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "")
if os.getenv("FALLBACK_API_KEY") and os.getenv("FALLBACK_BASE_URL"):
    fallback_client = OpenAI(
        api_key=os.getenv("FALLBACK_API_KEY"),
        base_url=os.getenv("FALLBACK_BASE_URL"),
    )
    print(f"🔄 Fallback 已配置: {FALLBACK_MODEL}")

# Token 用量追踪
tracker = TokenTracker(model=os.getenv("MODEL", "Vendor2/Claude-4.6-opus"))

# 2. 路径配置 (从环境变量读取，run.sh 统一管理)
BASE_DIR = os.getenv("BASE_DIR", "/data/haotianwu/biojson")
INPUT_DIR = os.getenv("MD_DIR", os.path.join(BASE_DIR, "md"))
REPORTS_DIR = os.getenv("REPORTS_DIR", os.path.join(BASE_DIR, "reports"))
PROMPT_PATH = os.getenv("PROMPT_PATH", os.path.join(BASE_DIR, "configs/nutri_gene_prompt_v2.txt"))
SCHEMA_PATH = os.getenv("SCHEMA_PATH", os.path.join(BASE_DIR, "configs/nutri_gene_schema_v2.json"))
TOKEN_USAGE_DIR = os.getenv("TOKEN_USAGE_DIR", os.path.join(BASE_DIR, "token-usage"))

# 确保输出目录存在
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(TOKEN_USAGE_DIR, exist_ok=True)


def stem_to_dirname(stem):
    """将 MD 文件名 stem 转为 reports 子目录名（GitHub 命名规范）。

    规则:
      - 去掉 'MinerU_markdown_' 前缀（如果有）
      - 去掉括号及其内容如 '_(1)'
      - 下划线转连字符
    """
    if stem.startswith("MinerU_markdown_"):
        stem = stem[len("MinerU_markdown_"):]
    stem = stem.replace("_(1)", "")
    stem = stem.replace("_", "-")
    return stem

# 3. 读取 Prompt 和 Schema
with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
    base_prompt = f.read()

with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
    template = json.load(f)
    paradigm = template.get("CropNutrientMetabolismGeneExtraction", template)

# 4. 构建 function_calling 的 tool 定义
# 将基因字段的 schema 转为 function parameters 格式
GENE_PROPERTIES = {}
gene_def = paradigm.get("$defs", {}).get("NutrientMetabolismGene", {})
for field_name, field_schema in gene_def.get("properties", {}).items():
    # 简化 anyOf 为 string 类型（function_calling 不支持 anyOf）
    desc = field_schema.get("description", "")
    if field_name == "Key_Intermediate_Metabolites_Affected" or field_name == "Interacting_Proteins":
        GENE_PROPERTIES[field_name] = {
            "type": "array",
            "items": {"type": "string"},
            "description": desc
        }
    else:
        GENE_PROPERTIES[field_name] = {
            "type": "string",
            "description": desc
        }

EXTRACT_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_nutrient_genes",
        "description": "Extract crop nutrient metabolism gene information from a scientific paper. "
                       "Extract ALL genes that are directly experimentally validated in the Results section. "
                       "If information is not found, use 'NA'.",
        "parameters": {
            "type": "object",
            "properties": {
                "Title": {
                    "type": "string",
                    "description": "Full paper title."
                },
                "Journal": {
                    "type": "string",
                    "description": "Journal name."
                },
                "DOI": {
                    "type": "string",
                    "description": "Pure DOI string, no URL prefix."
                },
                "Genes": {
                    "type": "array",
                    "description": "List of key gene objects (enzymes/regulators) impacting final nutrient products.",
                    "items": {
                        "type": "object",
                        "properties": GENE_PROPERTIES
                    }
                }
            },
            "required": ["Title", "Journal", "DOI", "Genes"]
        }
    }
}

# 5. 记录提取失败的文件（用于最终汇总）
failed_files = []


def resolve_test_files(files):
    """根据 TEST_INDEX 环境变量筛选测试文件，支持编号和文件名。"""
    test_index = os.getenv("TEST_INDEX", "1")

    # 纯数字 → 按编号
    if test_index.isdigit():
        idx = int(test_index) - 1  # 转为 0-based
        if 0 <= idx < len(files):
            print(f"🧪 测试模式: 仅处理第 {idx + 1} 个文件 → {files[idx]}")
            return [files[idx]]
        else:
            print(f"❌ 编号 {idx + 1} 超出范围 (共 {len(files)} 个文件)")
            return []

    # 非数字 → 按文件名匹配
    target = test_index if test_index.endswith(".md") else test_index + ".md"
    matched = [f for f in files if f == target]
    if matched:
        print(f"🧪 测试模式: 按文件名匹配 → {matched[0]}")
        return matched

    # 模糊匹配：文件名包含关键词
    matched = [f for f in files if test_index in f]
    if matched:
        if len(matched) == 1:
            print(f"🧪 测试模式: 模糊匹配 → {matched[0]}")
        else:
            print(f"🧪 测试模式: 模糊匹配到 {len(matched)} 个文件，取第一个 → {matched[0]}")
        return [matched[0]]

    print(f"❌ 未找到匹配 '{test_index}' 的文件 (共 {len(files)} 个文件)")
    return []


# 6. 核心提取逻辑

def _repair_truncated_json(json_str):
    """尝试修复被截断的 JSON 字符串。
    
    策略：
      1. 找到最后一个完整的 '}' 对象结尾
      2. 补全缺失的 ']' 和 '}'
    """
    # 先尝试直接解析
    try:
        return json.loads(json_str), False
    except json.JSONDecodeError:
        pass

    # 找到最后一个完整的基因对象（以 '}' 结尾）
    # 从后往前找最后一个 '}'
    last_brace = json_str.rfind('}')
    if last_brace == -1:
        return None, True

    # 截取到最后一个 '}' 并尝试补全
    truncated = json_str[:last_brace + 1]

    # 计算缺失的括号
    open_braces = truncated.count('{') - truncated.count('}')
    open_brackets = truncated.count('[') - truncated.count(']')

    # 补全
    repair = truncated + ']' * open_brackets + '}' * open_braces

    try:
        data = json.loads(repair)
        return data, True
    except json.JSONDecodeError:
        # 更激进的修复：找到 "Genes": [ 后的最后一个完整 },
        # 然后截断并补全
        genes_pos = json_str.find('"Genes"')
        if genes_pos == -1:
            return None, True

        # 从 Genes 数组开始，找每个 }, 的位置
        bracket_pos = json_str.find('[', genes_pos)
        if bracket_pos == -1:
            return None, True

        # 找最后一个 "}, " 或 "}," 模式（完整基因对象之间的分隔）
        import re
        # 匹配基因对象的结尾 }，后面跟 , 或空白
        endings = list(re.finditer(r'\}\s*,', json_str[bracket_pos:]))
        if not endings:
            return None, True

        last_complete = bracket_pos + endings[-1].end() - 1  # 指向 ','
        # 截取到最后一个完整对象，去掉尾部的逗号
        partial = json_str[:last_complete].rstrip(',').rstrip()

        # 计算缺失的括号并补全
        open_braces2 = partial.count('{') - partial.count('}')
        open_brackets2 = partial.count('[') - partial.count(']')
        repair2 = partial + '}' * max(0, open_braces2)  # 先补 }
        # 重新计算
        open_brackets2 = repair2.count('[') - repair2.count(']')
        repair2 = repair2 + ']' * max(0, open_brackets2)
        open_braces3 = repair2.count('{') - repair2.count('}')
        repair2 = repair2 + '}' * max(0, open_braces3)

        try:
            data = json.loads(repair2)
            return data, True
        except json.JSONDecodeError:
            return None, True


def _call_extract_api(api_client, model, content, name):
    """调用指定的 API 客户端进行提取，返回 (json_data, success) 元组。
    
    success 含义:
      - True:  成功提取到有 Genes 的结果
      - False: API 返回空内容 / 没有 Genes / 异常
    """
    try:
        response = api_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": base_prompt},
                {"role": "user", "content": f'Analyze this literature and extract all nutrient metabolism gene information:\n\n{content}'}
            ],
            tools=[EXTRACT_TOOL],
            tool_choice={"type": "function", "function": {"name": "extract_nutrient_genes"}},
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            max_tokens=16384,
        )

        # 记录 Token 用量
        tracker.add(response, stage="extract", file=name)

        message = response.choices[0].message

        has_tool_calls = message.tool_calls and len(message.tool_calls) > 0
        has_content = message.content and message.content.strip()

        if not has_tool_calls and not has_content:
            print(f"  ⚠️  [{model}] API 返回空内容: {name}")
            return None, False

        if has_tool_calls:
            tool_call = message.tool_calls[0]
            json_str = tool_call.function.arguments

            # 尝试解析 JSON，如果截断则自动修复
            json_data, was_repaired = _repair_truncated_json(json_str)
            if json_data is None:
                print(f"  ❌ [{model}] JSON 无法解析也无法修复: {name}")
                return None, False
            if was_repaired:
                genes_count = len(json_data.get("Genes", []))
                print(f"  🔧 [{model}] 截断 JSON 已自动修复 (抢救到 {genes_count} 个基因)")

            # 防御：LLM 偶发把 Genes 数组序列化为字符串
            if isinstance(json_data.get("Genes"), str):
                try:
                    json_data["Genes"] = json.loads(json_data["Genes"])
                    print(f"  🔧 自动修复: Genes 从字符串转为列表 ({len(json_data['Genes'])} 个基因)")
                except json.JSONDecodeError:
                    print(f"  ⚠️  Genes 是截断的字符串，无法自动修复")
            print(f"  ✅ [{model}] Function calling 成功提取")
        else:
            print(f"  ⚠️  [{model}] Function calling 未触发，回退到正则提取")
            raw_result = message.content or ""
            json_data = _fallback_extract_json(raw_result, name)

        # 检查是否有有效的 Genes
        genes = json_data.get("Genes", [])
        if isinstance(genes, list) and len(genes) == 0:
            print(f"  ⚠️  [{model}] 提取结果中 Genes 为空列表")
            return json_data, False

        return json_data, True

    except json.JSONDecodeError as e:
        print(f"  ❌ [{model}] JSON 解析失败: {name}: {e}")
        return None, False
    except Exception as e:
        print(f"  ❌ [{model}] 处理文件 {name} 时发生错误: {str(e)}")
        return None, False


def ai_response(path):
    name = os.path.basename(path)
    filename = os.path.splitext(name)[0]

    # 增量处理：如果输出已存在且未设置 FORCE_RERUN，跳过
    paper_dir = os.path.join(REPORTS_DIR, stem_to_dirname(filename))
    output_path = os.path.join(paper_dir, "extraction.json")
    if os.path.exists(output_path) and os.getenv("FORCE_RERUN") != "1":
        print(f"  ⏭️  已存在，跳过: {output_path}  (设置 FORCE_RERUN=1 强制重跑)")
        return

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 文本预处理：去除图片、引用列表、致谢等无用内容，减少 token 消耗
    original_len = len(content)
    content = preprocess_md(content)
    print(f"  📏 文本预处理: {original_len:,} → {len(content):,} 字符 (节省 {original_len - len(content):,} 字符)")

    primary_model = os.getenv("MODEL", "Vendor2/Claude-4.6-opus")

    # ── 第一次尝试：主 API ─────────────────────────────────────────────────
    print(f"  🔵 使用主 API ({primary_model}) 提取...")
    json_data, success = _call_extract_api(client, primary_model, content, name)

    # ── Fallback：如果主 API 失败且 DeepSeek fallback 可用 ─────────────────
    if not success and fallback_client:
        print(f"  🔄 主 API 失败，自动切换到 Fallback ({FALLBACK_MODEL})...")
        json_data, success = _call_extract_api(fallback_client, FALLBACK_MODEL, content, name)

    # ── 处理最终结果 ──────────────────────────────────────────────────────
    if not success or json_data is None:
        print(f"  ⚠️  所有 API 均失败: {name}")
        failed_files.append(name)
        os.makedirs(paper_dir, exist_ok=True)
        error_report = {
            "file": name,
            "error": "All APIs failed (empty response or no Genes)",
            "timestamp": datetime.now().isoformat(),
        }
        error_path = os.path.join(paper_dir, "extraction-error.json")
        with open(error_path, 'w', encoding='utf-8') as f:
            json.dump(error_report, f, indent=2, ensure_ascii=False)
        print(f"  📋 错误已记录: {error_path}")
        return

    final_output = json.dumps(json_data, indent=2, ensure_ascii=False)

    # 保存结果到 reports/{paper-dir}/extraction.json
    os.makedirs(paper_dir, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_output)

    print(f"  ✅ 成功处理: {name} -> {output_path}")


def _fallback_extract_json(raw_result, name):
    """回退方案：从文本中提取 JSON（兼容不支持 function_calling 的情况）"""
    import re
    
    # 优先提取 <structured_information> 标签内的内容
    tag_match = re.search(r'<structured_information>(.*?)</structured_information>', raw_result, re.DOTALL)
    if tag_match:
        clean_json = tag_match.group(1).strip()
    else:
        # 备选 1：尝试匹配 Markdown 代码块
        code_match = re.search(r'```json\s*(.*?)\s*```', raw_result, re.DOTALL)
        if code_match:
            clean_json = code_match.group(1).strip()
        else:
            # 备选 2：强力提取第一个 { 到最后一个 } 之间的内容
            brace_match = re.search(r'(\{.*\})', raw_result, re.DOTALL)
            clean_json = brace_match.group(1).strip() if brace_match else raw_result

    try:
        return json.loads(clean_json)
    except json.JSONDecodeError:
        print(f"  ⚠️  Fallback JSON 解析也失败: {name}")
        return {"error": "JSON parse failed", "raw": clean_json[:500]}


# 7. 遍历执行
if __name__ == "__main__":
    if not os.path.exists(INPUT_DIR):
        print(f"错误: 输入目录 {INPUT_DIR} 不存在！")
    else:
        files = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith('.md')])
        print(f"找到 {len(files)} 个待处理文件...")

        # 测试模式：支持编号和文件名
        if os.getenv("TEST_MODE") == "1":
            files = resolve_test_files(files)

        for file in files:
            ai_response(os.path.join(INPUT_DIR, file))

        # 打印 Token 用量汇总并保存报告
        tracker.print_summary()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tracker.save_report(os.path.join(TOKEN_USAGE_DIR, f"extract-{timestamp}.json"))

        # 汇总提醒：API 返回空内容的文件
        if failed_files:
            print(f"\n{'='*60}")
            print(f"⚠️  以下 {len(failed_files)} 个文件 API 返回空内容，需要重跑:")
            for f in failed_files:
                print(f"     - {f}")
            print(f"   提示: FORCE_RERUN=1 bash scripts/run.sh extract")
            print(f"{'='*60}")
