"""
md_to_json.py  (v2 — 拆分 tool 架构)

提取模块：给 LLM 提供 4 个 tools（classify + 3×extract），
一次 API 调用完成基因分类 + 详细字段提取。

对外暴露:
    extract_paper(md_path) -> (extraction_dict, gene_dict)
    供 pipeline.py 调用。

也可独立运行:
    python scripts/md_to_json.py
"""

import json
import os
import re
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from token_tracker import TokenTracker
from text_utils import preprocess_md

load_dotenv()

# ─── 客户端初始化 ────────────────────────────────────────────────────────────────
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

fallback_client = None
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "")
if os.getenv("FALLBACK_API_KEY") and os.getenv("FALLBACK_BASE_URL"):
    fallback_client = OpenAI(
        api_key=os.getenv("FALLBACK_API_KEY"),
        base_url=os.getenv("FALLBACK_BASE_URL"),
    )
    print(f"🔄 Fallback 已配置: {FALLBACK_MODEL}")

tracker = TokenTracker(model=os.getenv("MODEL", "Vendor2/Claude-4.6-opus"))

# ─── 路径配置 ─────────────────────────────────────────────────────────────────────
BASE_DIR = os.getenv("BASE_DIR", "/data/haotianwu/biojson")
INPUT_DIR = os.getenv("MD_DIR", os.path.join(BASE_DIR, "md"))
REPORTS_DIR = os.getenv("REPORTS_DIR", os.path.join(BASE_DIR, "reports"))
PROMPT_PATH = os.getenv("PROMPT_PATH", os.path.join(BASE_DIR, "configs/nutri_gene_prompt_v2.txt"))
SCHEMA_PATH = os.getenv("SCHEMA_PATH", os.path.join(BASE_DIR, "configs/nutri_gene_schema_v2.json"))
TOKEN_USAGE_DIR = os.getenv("TOKEN_USAGE_DIR", os.path.join(BASE_DIR, "token-usage"))

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(TOKEN_USAGE_DIR, exist_ok=True)


def stem_to_dirname(stem):
    """将 MD 文件名 stem 转为 reports 子目录名（GitHub 命名规范）。"""
    if stem.startswith("MinerU_markdown_"):
        stem = stem[len("MinerU_markdown_"):]
    stem = stem.replace("_(1)", "")
    stem = stem.replace("_", "-")
    return stem


# ─── 读取 Prompt 和 Schema ───────────────────────────────────────────────────────
with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
    base_prompt = f.read()

with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
    schema_all = json.load(f)


# ─── 辅助：schema → function calling 格式 ────────────────────────────────────────

def _schema_props_to_fc(gene_def):
    """将 nutri_gene_schema_v2.json 中一个 Gene 类型的 properties 转为
    function calling 兼容格式（anyOf → string，保留 description）。"""
    fc_props = {}
    for field_name, field_schema in gene_def.get("properties", {}).items():
        desc = field_schema.get("description", "")
        fc_props[field_name] = {"type": "string", "description": desc}
    return fc_props


# 从各自独立的 Extraction 定义中读取字段
_common_defs = schema_all.get("CommonGeneExtraction", {}).get("$defs", {})
_pathway_defs = schema_all.get("PathwayGeneExtraction", {}).get("$defs", {})
_regulation_defs = schema_all.get("RegulationGeneExtraction", {}).get("$defs", {})

COMMON_GENE_PROPS = _schema_props_to_fc(_common_defs.get("CommonGene", {}))
PATHWAY_GENE_PROPS = _schema_props_to_fc(_pathway_defs.get("PathwayGene", {}))
REGULATION_GENE_PROPS = _schema_props_to_fc(_regulation_defs.get("RegulationGene", {}))

print(f"📋 Schema 字段数: Common={len(COMMON_GENE_PROPS)}, "
      f"Pathway={len(PATHWAY_GENE_PROPS)}, Regulation={len(REGULATION_GENE_PROPS)}")


# ═══════════════════════════════════════════════════════════════════════════════════
#  4 个 Tools 定义
# ═══════════════════════════════════════════════════════════════════════════════════

CLASSIFY_TOOL = {
    "type": "function",
    "function": {
        "name": "classify_genes",
        "description": (
            "Identify ALL core genes from the paper's Results section and classify each into one of three categories:\n"
            "- Common: genes that are neither pathway enzymes nor regulators (e.g., general functional genes)\n"
            "- Pathway: genes encoding enzymes in biosynthetic/metabolic pathways (e.g., CHS, F3H, PSY, DAHPS)\n"
            "- Regulation: genes encoding transcription factors, signaling proteins, or other regulators (e.g., MYB12, Del, Ros1, SPL)\n"
            "Only include genes that are directly experimentally validated in the Results section."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "Title": {"type": "string", "description": "Full paper title."},
                "Journal": {"type": "string", "description": "Journal name."},
                "DOI": {"type": "string", "description": "Pure DOI string, no URL prefix."},
                "genes": {
                    "type": "array",
                    "description": "List of all core genes identified from the paper.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "Gene_Name": {"type": "string", "description": "Gene name or symbol."},
                            "category": {
                                "type": "string",
                                "enum": ["Common", "Pathway", "Regulation"],
                                "description": "Gene category."
                            },
                            "reason": {"type": "string", "description": "Brief reason for classification."}
                        },
                        "required": ["Gene_Name", "category"]
                    }
                }
            },
            "required": ["Title", "Journal", "DOI", "genes"]
        }
    }
}

EXTRACT_COMMON_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_common_genes",
        "description": (
            "Extract detailed field information for Common genes (genes that are neither pathway enzymes nor regulators). "
            "Only call this tool if classify_genes identified Common genes. "
            "If information is not found, use 'NA'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "genes": {
                    "type": "array",
                    "description": "Detailed information for each Common gene.",
                    "items": {"type": "object", "properties": COMMON_GENE_PROPS}
                }
            },
            "required": ["genes"]
        }
    }
}

EXTRACT_PATHWAY_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_pathway_genes",
        "description": (
            "Extract detailed field information for Pathway genes (genes encoding enzymes in biosynthetic/metabolic pathways). "
            "Only call this tool if classify_genes identified Pathway genes. "
            "If information is not found, use 'NA'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "genes": {
                    "type": "array",
                    "description": "Detailed information for each Pathway gene.",
                    "items": {"type": "object", "properties": PATHWAY_GENE_PROPS}
                }
            },
            "required": ["genes"]
        }
    }
}

EXTRACT_REGULATION_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_regulation_genes",
        "description": (
            "Extract detailed field information for Regulation genes (transcription factors, signaling proteins, regulators). "
            "Only call this tool if classify_genes identified Regulation genes. "
            "If information is not found, use 'NA'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "genes": {
                    "type": "array",
                    "description": "Detailed information for each Regulation gene.",
                    "items": {"type": "object", "properties": REGULATION_GENE_PROPS}
                }
            },
            "required": ["genes"]
        }
    }
}

ALL_EXTRACT_TOOLS = [CLASSIFY_TOOL, EXTRACT_COMMON_TOOL, EXTRACT_PATHWAY_TOOL, EXTRACT_REGULATION_TOOL]

# tool name → array key 映射
_TOOL_TO_ARRAY_KEY = {
    "extract_common_genes": "Common_Genes",
    "extract_pathway_genes": "Pathway_Genes",
    "extract_regulation_genes": "Regulation_Genes",
}


# ═══════════════════════════════════════════════════════════════════════════════════
#  核心提取逻辑
# ═══════════════════════════════════════════════════════════════════════════════════

failed_files = []


def _repair_truncated_json(json_str):
    """尝试修复被截断的 JSON 字符串。"""
    try:
        return json.loads(json_str), False
    except json.JSONDecodeError:
        pass

    last_brace = json_str.rfind('}')
    if last_brace == -1:
        return None, True

    truncated = json_str[:last_brace + 1]
    open_braces = truncated.count('{') - truncated.count('}')
    open_brackets = truncated.count('[') - truncated.count(']')
    repair = truncated + ']' * open_brackets + '}' * open_braces

    try:
        data = json.loads(repair)
        return data, True
    except json.JSONDecodeError:
        # 更激进的修复
        endings = list(re.finditer(r'\}\s*,', json_str))
        if not endings:
            return None, True
        last_complete = endings[-1].end() - 1
        partial = json_str[:last_complete].rstrip(',').rstrip()
        ob = partial.count('{') - partial.count('}')
        repair2 = partial + '}' * max(0, ob)
        ob2 = repair2.count('[') - repair2.count(']')
        repair2 = repair2 + ']' * max(0, ob2)
        ob3 = repair2.count('{') - repair2.count('}')
        repair2 = repair2 + '}' * max(0, ob3)
        try:
            return json.loads(repair2), True
        except json.JSONDecodeError:
            return None, True


def _safe_parse_tool_args(json_str, tool_name):
    """安全解析 tool call 的 arguments，支持截断修复。"""
    data, was_repaired = _repair_truncated_json(json_str)
    if data is None:
        print(f"  ❌ [{tool_name}] JSON 无法解析也无法修复")
        return None
    if was_repaired:
        print(f"  🔧 [{tool_name}] 截断 JSON 已自动修复")
    return data


def _fix_string_genes(data, key="genes"):
    """防御：LLM 偶发把数组序列化为字符串。"""
    arr = data.get(key)
    if isinstance(arr, str):
        try:
            data[key] = json.loads(arr)
            print(f"  🔧 自动修复: {key} 从字符串转为列表 ({len(data[key])} 个)")
        except json.JSONDecodeError:
            print(f"  ⚠️  {key} 是截断的字符串，无法自动修复")
    return data


def _call_extract_api(api_client, model, content, name):
    """调用 API 进行提取（4 个 tools），返回 (extraction_dict, gene_dict, success)。

    extraction_dict: {"Title":..., "Common_Genes":[...], "Pathway_Genes":[...], "Regulation_Genes":[...]}
    gene_dict: {"CHS": "Pathway", "MYB12": "Regulation", ...}
    """
    try:
        response = api_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": base_prompt},
                {"role": "user", "content": (
                    "Analyze this literature and extract all nutrient metabolism gene information.\n\n"
                    "IMPORTANT: You have 4 tools available. You MUST:\n"
                    "1. First call classify_genes to identify and classify all core genes.\n"
                    "2. Then call the appropriate extract_*_genes tools based on the categories found.\n"
                    "   - If there are Pathway genes, call extract_pathway_genes\n"
                    "   - If there are Regulation genes, call extract_regulation_genes\n"
                    "   - If there are Common genes, call extract_common_genes\n"
                    "3. Call ALL relevant extract tools in a single response (parallel tool calls).\n\n"
                    f"Paper content:\n\n{content}"
                )}
            ],
            tools=ALL_EXTRACT_TOOLS,
            tool_choice="auto",
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            max_tokens=16384,
        )

        tracker.add(response, stage="extract", file=name)
        message = response.choices[0].message

        if not message.tool_calls or len(message.tool_calls) == 0:
            print(f"  ⚠️  [{model}] 未触发任何 tool call: {name}")
            return None, None, False

        # 解析所有 tool calls
        classify_result = None
        extraction = {"Common_Genes": [], "Pathway_Genes": [], "Regulation_Genes": []}
        gene_dict = {}

        for tc in message.tool_calls:
            fn_name = tc.function.name
            data = _safe_parse_tool_args(tc.function.arguments, fn_name)
            if data is None:
                continue

            if fn_name == "classify_genes":
                classify_result = data
                # 构建 gene_dict
                genes_list = data.get("genes", [])
                if isinstance(genes_list, str):
                    try:
                        genes_list = json.loads(genes_list)
                    except json.JSONDecodeError:
                        genes_list = []
                for g in genes_list:
                    gname = g.get("Gene_Name", "")
                    cat = g.get("category", "Common")
                    if gname:
                        gene_dict[gname] = cat
                print(f"  ✅ [{model}] classify_genes: {len(gene_dict)} 个基因")

            elif fn_name in _TOOL_TO_ARRAY_KEY:
                arr_key = _TOOL_TO_ARRAY_KEY[fn_name]
                data = _fix_string_genes(data, "genes")
                genes_arr = data.get("genes", [])
                if isinstance(genes_arr, list):
                    extraction[arr_key] = genes_arr
                    print(f"  ✅ [{model}] {fn_name}: {len(genes_arr)} 个基因")
                else:
                    print(f"  ⚠️  [{model}] {fn_name}: genes 不是列表")

            else:
                print(f"  ⚠️  [{model}] 未知 tool: {fn_name}")

        # 合并论文级元数据
        if classify_result:
            extraction["Title"] = classify_result.get("Title", "NA")
            extraction["Journal"] = classify_result.get("Journal", "NA")
            extraction["DOI"] = classify_result.get("DOI", "NA")

        # 统计
        c = len(extraction.get("Common_Genes", []))
        p = len(extraction.get("Pathway_Genes", []))
        r = len(extraction.get("Regulation_Genes", []))
        total = c + p + r

        if total == 0:
            print(f"  ⚠️  [{model}] 提取结果中所有基因数组均为空")
            return extraction, gene_dict, False

        print(f"  📊 基因提取: Common={c}, Pathway={p}, Regulation={r}, 总计={total}")
        return extraction, gene_dict, True

    except Exception as e:
        print(f"  ❌ [{model}] 处理文件 {name} 时发生错误: {str(e)}")
        return None, None, False


def extract_paper(md_path):
    """提取单篇论文的基因信息。

    Args:
        md_path: MD 文件路径

    Returns:
        (extraction_dict, gene_dict) 或 (None, None) 如果失败
        extraction_dict: {"Title":..., "Common_Genes":[...], "Pathway_Genes":[...], "Regulation_Genes":[...]}
        gene_dict: {"CHS": "Pathway", "MYB12": "Regulation", ...}
    """
    name = os.path.basename(md_path)
    filename = os.path.splitext(name)[0]

    # 增量处理
    paper_dir = os.path.join(REPORTS_DIR, stem_to_dirname(filename))
    output_path = os.path.join(paper_dir, "extraction.json")
    if os.path.exists(output_path) and os.getenv("FORCE_RERUN") != "1":
        print(f"  ⏭️  已存在，跳过: {output_path}  (设置 FORCE_RERUN=1 强制重跑)")
        # 从已有文件恢复
        with open(output_path, 'r', encoding='utf-8') as f:
            extraction = json.load(f)
        gene_dict_path = os.path.join(paper_dir, "gene_dict.json")
        gene_dict = {}
        if os.path.exists(gene_dict_path):
            with open(gene_dict_path, 'r', encoding='utf-8') as f:
                gene_dict = json.load(f)
        else:
            # 从 extraction 重建 gene_dict
            for arr_key, cat in [("Common_Genes", "Common"), ("Pathway_Genes", "Pathway"), ("Regulation_Genes", "Regulation")]:
                for g in extraction.get(arr_key, []):
                    if isinstance(g, dict):
                        gname = g.get("Gene_Name", "")
                        if gname:
                            gene_dict[gname] = cat
        return extraction, gene_dict

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_len = len(content)
    content = preprocess_md(content)
    print(f"  📏 文本预处理: {original_len:,} → {len(content):,} 字符 (节省 {original_len - len(content):,} 字符)")

    primary_model = os.getenv("MODEL", "Vendor2/Claude-4.6-opus")

    # 第一次尝试：主 API
    print(f"  🔵 使用主 API ({primary_model}) 提取...")
    extraction, gene_dict, success = _call_extract_api(client, primary_model, content, name)

    # Fallback
    if not success and fallback_client:
        print(f"  🔄 主 API 失败，自动切换到 Fallback ({FALLBACK_MODEL})...")
        extraction, gene_dict, success = _call_extract_api(fallback_client, FALLBACK_MODEL, content, name)

    if not success or extraction is None:
        print(f"  ⚠️  所有 API 均失败: {name}")
        failed_files.append(name)
        os.makedirs(paper_dir, exist_ok=True)
        error_report = {
            "file": name,
            "error": "All APIs failed",
            "timestamp": datetime.now().isoformat(),
        }
        with open(os.path.join(paper_dir, "extraction-error.json"), 'w', encoding='utf-8') as f:
            json.dump(error_report, f, indent=2, ensure_ascii=False)
        return None, None

    # 保存结果
    os.makedirs(paper_dir, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(extraction, f, indent=2, ensure_ascii=False)
    print(f"  ✅ 提取结果已保存: {output_path}")

    # 保存 gene_dict（备份，供断点恢复）
    if gene_dict:
        gene_dict_path = os.path.join(paper_dir, "gene_dict.json")
        with open(gene_dict_path, 'w', encoding='utf-8') as f:
            json.dump(gene_dict, f, indent=2, ensure_ascii=False)
        print(f"  📋 基因分类字典已保存: {gene_dict_path}")

    return extraction, gene_dict


# ═══════════════════════════════════════════════════════════════════════════════════
#  旧版兼容入口 ai_response()（供旧的 run.sh extract 模式使用）
# ═══════════════════════════════════════════════════════════════════════════════════

def ai_response(path):
    """旧版兼容入口：仅提取，不返回结果。"""
    extract_paper(path)


def resolve_test_files(files):
    """根据 TEST_INDEX 环境变量筛选测试文件。"""
    test_index = os.getenv("TEST_INDEX", "1")
    if test_index.isdigit():
        idx = int(test_index) - 1
        if 0 <= idx < len(files):
            print(f"🧪 测试模式: 仅处理第 {idx + 1} 个文件 → {files[idx]}")
            return [files[idx]]
        else:
            print(f"❌ 编号 {idx + 1} 超出范围 (共 {len(files)} 个文件)")
            return []
    target = test_index if test_index.endswith(".md") else test_index + ".md"
    matched = [f for f in files if f == target]
    if matched:
        print(f"🧪 测试模式: 按文件名匹配 → {matched[0]}")
        return matched
    matched = [f for f in files if test_index in f]
    if matched:
        print(f"🧪 测试模式: 模糊匹配 → {matched[0]}")
        return [matched[0]]
    print(f"❌ 未找到匹配 '{test_index}' 的文件 (共 {len(files)} 个文件)")
    return []


if __name__ == "__main__":
    if not os.path.exists(INPUT_DIR):
        print(f"错误: 输入目录 {INPUT_DIR} 不存在！")
    else:
        files = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith('.md')])
        print(f"找到 {len(files)} 个待处理文件...")

        if os.getenv("TEST_MODE") == "1":
            files = resolve_test_files(files)

        for file in files:
            ai_response(os.path.join(INPUT_DIR, file))

        tracker.print_summary()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tracker.save_report(os.path.join(TOKEN_USAGE_DIR, f"extract-{timestamp}.json"))

        if failed_files:
            print(f"\n{'='*60}")
            print(f"⚠️  以下 {len(failed_files)} 个文件 API 返回空内容，需要重跑:")
            for f in failed_files:
                print(f"     - {f}")
            print(f"   提示: FORCE_RERUN=1 bash scripts/run.sh extract")
            print(f"{'='*60}")
