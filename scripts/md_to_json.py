import json
import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from token_tracker import TokenTracker
from text_utils import strip_references
load_dotenv()

# 1. 初始化客户端
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")  # 确保加上了 /v1
)

# Token 用量追踪
tracker = TokenTracker(model=os.getenv("MODEL", "Vendor2/Claude-4.6-opus"))

# 2. 路径配置 (从环境变量读取，run.sh 统一管理)
BASE_DIR = os.getenv("BASE_DIR", "/data/haotianwu/biojson")
INPUT_DIR = os.getenv("MD_DIR", os.path.join(BASE_DIR, "md"))
OUTPUT_DIR = os.getenv("RAW_EXTRACTIONS_DIR", os.path.join(BASE_DIR, "reports/raw_extractions"))
PROMPT_PATH = os.getenv("PROMPT_PATH", os.path.join(BASE_DIR, "configs/nutri_plant.txt"))
SCHEMA_PATH = os.getenv("SCHEMA_PATH", os.path.join(BASE_DIR, "configs/nutri_plant.json"))
EXTRACT_TOKENS_DIR = os.getenv("EXTRACT_TOKENS_DIR", os.path.join(BASE_DIR, "reports/extract_tokens"))

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(EXTRACT_TOKENS_DIR, exist_ok=True)

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

# 5. 核心提取逻辑
def ai_response(path):
    name = os.path.basename(path)
    filename = os.path.splitext(name)[0]

    # 增量处理：如果输出已存在且未设置 FORCE_RERUN，跳过
    output_path = os.path.join(OUTPUT_DIR, f'{filename}_nutri_plant.json')
    if os.path.exists(output_path) and os.getenv("FORCE_RERUN") != "1":
        print(f"  ⏭️  已存在，跳过: {output_path}  (设置 FORCE_RERUN=1 强制重跑)")
        return

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 去除 References 引用列表，保留后面有用的 section（如 STAR Methods）
    original_len = len(content)
    content = strip_references(content)
    print(f"  📏 文本预处理: {original_len:,} → {len(content):,} 字符 (去除 References 列表节省 {original_len - len(content):,} 字符)")

    try:
        response = client.chat.completions.create(
            model=os.getenv("MODEL", "Vendor2/Claude-4.6-opus"),
            messages=[
                {"role": "system", "content": base_prompt},
                {"role": "user", "content": f'Analyze this literature and extract all nutrient metabolism gene information:\n\n{content}'}
            ],
            tools=[EXTRACT_TOOL],
            tool_choice={"type": "function", "function": {"name": "extract_nutrient_genes"}},
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
        )
        
        # 记录 Token 用量
        tracker.add(response, stage="extract", file=name)
        
        # 从 function_calling 响应中提取 JSON
        message = response.choices[0].message
        
        if message.tool_calls and len(message.tool_calls) > 0:
            # ✅ 成功走 function_calling 路径
            tool_call = message.tool_calls[0]
            json_str = tool_call.function.arguments
            json_data = json.loads(json_str)
            # 防御：LLM 偶发把 Genes 数组序列化为字符串
            if isinstance(json_data.get("Genes"), str):
                try:
                    json_data["Genes"] = json.loads(json_data["Genes"])
                    print(f"  🔧 自动修复: Genes 从字符串转为列表 ({len(json_data['Genes'])} 个基因)")
                except json.JSONDecodeError:
                    print(f"  ⚠️  Genes 是截断的字符串，无法自动修复，需要重新提取")
            print(f"  ✅ Function calling 成功提取")
        else:
            # Fallback: 如果 API 不支持 function_calling，回退到正则提取
            print(f"  ⚠️  Function calling 未触发，回退到正则提取")
            raw_result = message.content or ""
            json_data = _fallback_extract_json(raw_result, name)

        final_output = json.dumps(json_data, indent=2, ensure_ascii=False)

        # 保存结果
        output_path = os.path.join(OUTPUT_DIR, f'{filename}_nutri_plant.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_output)
        
        print(f"  ✅ 成功处理: {name} -> {output_path}")

    except json.JSONDecodeError as e:
        print(f"  ❌ JSON 解析失败: {name}: {e}")
    except Exception as e:
        print(f"  ❌ 处理文件 {name} 时发生错误: {str(e)}")


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


# 6. 遍历执行
if __name__ == "__main__":
    if not os.path.exists(INPUT_DIR):
        print(f"错误: 输入目录 {INPUT_DIR} 不存在！")
    else:
        files = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith('.md')])
        print(f"找到 {len(files)} 个待处理文件...")

        # 测试模式：仅处理指定编号的文件
        if os.getenv("TEST_MODE") == "1":
            idx = int(os.getenv("TEST_INDEX", "1")) - 1  # 转为 0-based
            if 0 <= idx < len(files):
                files = [files[idx]]
                print(f"🧪 测试模式: 仅处理第 {idx + 1} 个文件 → {files[0]}")
            else:
                print(f"❌ 编号 {idx + 1} 超出范围 (共 {len(files)} 个文件)")
                files = []

        for file in files:
            ai_response(os.path.join(INPUT_DIR, file))

        # 打印 Token 用量汇总并保存报告
        tracker.print_summary()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tracker.save_report(os.path.join(EXTRACT_TOKENS_DIR, f"token_usage_extract_{timestamp}.json"))
