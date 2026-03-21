"""
handlers.py — Tool handlers for biojson-extraction skill

每个 handler 签名: handler(arguments: dict, state: dict) -> str
  - arguments: LLM 传来的参数（已解析为 dict）
  - state: ToolRegistry 的共享状态（handlers 之间传递数据）
  - 返回: tool_result 字符串（送回给 LLM 继续对话）

state 约定的 key:
  - "gene_dict": {Gene_Name: category} 映射
  - "extraction": {"Title":..., "Common_Genes":[], "Pathway_Genes":[], "Regulation_Genes":[]}
  - "verify_results": [gene_verdicts_list]
"""

import json


# ═══════════════════════════════════════════════════════════════════════════════════
#  提取阶段 handlers
# ═══════════════════════════════════════════════════════════════════════════════════

def handle_classify(arguments, state):
    """处理 classify_genes tool call。

    从 LLM 返回的分类结果中：
    1. 提取论文元数据（Title, Journal, DOI）
    2. 构建 gene_dict {Gene_Name: category}
    3. 存入 state 供后续 extract handlers 使用
    """
    # 初始化 state
    if "extraction" not in state:
        state["extraction"] = {
            "Common_Genes": [],
            "Pathway_Genes": [],
            "Regulation_Genes": [],
        }
    if "gene_dict" not in state:
        state["gene_dict"] = {}

    # 提取元数据
    state["extraction"]["Title"] = arguments.get("Title", "NA")
    state["extraction"]["Journal"] = arguments.get("Journal", "NA")
    state["extraction"]["DOI"] = arguments.get("DOI", "NA")

    # 解析基因列表
    genes_list = arguments.get("genes", [])
    if isinstance(genes_list, str):
        try:
            genes_list = json.loads(genes_list)
        except json.JSONDecodeError:
            genes_list = []

    # 构建 gene_dict（兼容主 API 返回的非标准字段名）
    # 标准 schema: {"Gene_Name": "CHS", "category": "Pathway"}
    # 主 API 可能返回: {"gene": "CHS", "category": "Enzymatic / Biosynthesis"}
    CATEGORY_MAP = {
        "Enzymatic / Biosynthesis": "Pathway",
        "Transcription factor / Regulatory": "Regulation",
        "Transcription Factor / Regulatory": "Regulation",
        "enzymatic / biosynthesis": "Pathway",
        "transcription factor / regulatory": "Regulation",
        "Enzymatic": "Pathway",
        "Biosynthesis": "Pathway",
        "Transcription factor": "Regulation",
        "Regulatory": "Regulation",
        "biosynthesis": "Pathway",
        "regulatory": "Regulation",
        "transcription factor": "Regulation",
        "enzyme": "Pathway",
        "Enzyme": "Pathway",
    }

    gene_dict = {}
    categories_summary = {"Common": 0, "Pathway": 0, "Regulation": 0}

    for g in genes_list:
        if not isinstance(g, dict):
            continue
        # 字段名兼容: Gene_Name / gene / name / gene_name
        gname = (g.get("Gene_Name")
                 or g.get("gene")
                 or g.get("gene_name")
                 or g.get("name")
                 or "")
        # category 兼容映射
        cat = g.get("category", "Common")
        cat = CATEGORY_MAP.get(cat, cat)
        if cat not in ("Common", "Pathway", "Regulation"):
            cat = "Common"  # 兜底
        if gname:
            gene_dict[gname] = cat
            categories_summary[cat] = categories_summary.get(cat, 0) + 1

    state["gene_dict"] = gene_dict

    # 构建反馈消息（告诉 LLM 分类结果，引导它继续调用 extract tools）
    summary_parts = []
    for cat, count in categories_summary.items():
        if count > 0:
            genes_in_cat = [name for name, c in gene_dict.items() if c == cat]
            summary_parts.append(f"{cat}: {', '.join(genes_in_cat)}")

    result = (
        f"Classification received: {len(gene_dict)} genes identified.\n"
        + "\n".join(summary_parts)
        + "\n\nNow please call the appropriate extract_*_genes tools for each category "
        "to extract detailed field information."
    )

    print(f"      📋 classify: {len(gene_dict)} 个基因 — {categories_summary}")
    return result


def handle_extract_common(arguments, state):
    """处理 extract_common_genes tool call。"""
    return _handle_extract(arguments, state, "Common_Genes", "Common")


def handle_extract_pathway(arguments, state):
    """处理 extract_pathway_genes tool call。"""
    return _handle_extract(arguments, state, "Pathway_Genes", "Pathway")


def handle_extract_regulation(arguments, state):
    """处理 extract_regulation_genes tool call。"""
    return _handle_extract(arguments, state, "Regulation_Genes", "Regulation")


def _handle_extract(arguments, state, arr_key, category):
    """通用 extract handler。

    解析 LLM 返回的基因详细字段，存入 state["extraction"][arr_key]。
    """
    if "extraction" not in state:
        state["extraction"] = {
            "Common_Genes": [],
            "Pathway_Genes": [],
            "Regulation_Genes": [],
        }

    # 解析 genes 数组
    genes_arr = arguments.get("genes", [])
    if isinstance(genes_arr, str):
        try:
            genes_arr = json.loads(genes_arr)
            print(f"      🔧 自动修复: {arr_key} 从字符串转为列表 ({len(genes_arr)} 个)")
        except json.JSONDecodeError:
            print(f"      ⚠️  {arr_key} 是截断的字符串，无法自动修复")
            genes_arr = []

    if isinstance(genes_arr, list):
        state["extraction"][arr_key] = genes_arr
        count = len(genes_arr)
        print(f"      ✅ {arr_key}: {count} 个基因提取完成")
        return f"Received {count} {category} genes with detailed fields. Extraction complete for this category."
    else:
        print(f"      ⚠️  {arr_key}: genes 不是列表")
        return f"Error: genes field is not an array for {category}."


# ═══════════════════════════════════════════════════════════════════════════════════
#  验证阶段 handler
# ═══════════════════════════════════════════════════════════════════════════════════

def handle_verify_all(arguments, state):
    """处理 verify_all_genes tool call。

    解析 LLM 返回的验证结果，存入 state["verify_results"]。
    """
    gene_verdicts = arguments.get("gene_verdicts", [])
    if isinstance(gene_verdicts, str):
        try:
            gene_verdicts = json.loads(gene_verdicts)
        except json.JSONDecodeError:
            gene_verdicts = []

    state["verify_results"] = gene_verdicts

    total_fields = sum(len(gv.get("field_verdicts", [])) for gv in gene_verdicts)
    print(f"      ✅ 验证完成: {len(gene_verdicts)} 个基因, {total_fields} 个字段")

    return f"Verification received: {len(gene_verdicts)} genes, {total_fields} fields verified."
