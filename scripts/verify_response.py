"""
verify_response.py  (v2 — 一次性验证所有基因)

验证模块：一次 API 调用验证所有基因的所有非 NA 字段。
MD 文件只读入一次，大幅降低 token 消耗。

对外暴露:
    verify_paper(md_path, extraction_dict, gene_dict, stem) -> verification_report
    供 pipeline.py 调用。

也可独立运行:
    python scripts/verify_response.py
"""

import json
import os
import re
import shutil
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from token_tracker import TokenTracker
from text_utils import preprocess_md

load_dotenv()

# ─── 配置 ────────────────────────────────────────────────────────────────────────
BASE_DIR = os.getenv("BASE_DIR", "/data/haotianwu/biojson")
MD_DIR = os.getenv("MD_DIR", os.path.join(BASE_DIR, "md"))
REPORTS_DIR = os.getenv("REPORTS_DIR", os.path.join(BASE_DIR, "reports"))
FINAL_JSON_DIR = os.getenv("JSON_DIR", os.path.join(BASE_DIR, "json"))
TOKEN_USAGE_DIR = os.getenv("TOKEN_USAGE_DIR", os.path.join(BASE_DIR, "token-usage"))
PROCESSED_DIR = os.getenv("PROCESSED_DIR", os.path.join(MD_DIR, "processed"))

os.makedirs(FINAL_JSON_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(TOKEN_USAGE_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


def stem_to_dirname(stem):
    """将 MD 文件名 stem 转为 reports 子目录名。"""
    if stem.startswith("MinerU_markdown_"):
        stem = stem[len("MinerU_markdown_"):]
    stem = stem.replace("_(1)", "")
    stem = stem.replace("_", "-")
    return stem


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
    print(f"🔄 验证 Fallback 已配置: {FALLBACK_MODEL}")

MODEL = os.getenv("MODEL", "Vendor2/Claude-4.6-opus")
tracker = TokenTracker(model=MODEL)

# ─── 验证 Prompt ────────────────────────────────────────────────────────────────
VERIFY_SYSTEM_PROMPT = (
    "You are a rigorous academic verification assistant specializing in plant molecular biology "
    "and metabolic biochemistry.\n\n"
    "Your task: Given a scientific paper (Markdown) and extracted JSON fields for ALL genes, "
    "verify whether EACH field value is faithfully supported by the original paper.\n\n"
    "### Verification criteria:\n"
    "1. Core gene validity - Was this gene directly tested in the Results section?\n"
    "2. Trait validity - Is the gene linked to a final nutrient product, not just a generic trait?\n"
    "3. Directionality consistency - Do intermediate metabolite changes match the final product change?\n"
    "4. Evidence alignment - Are claims backed by figures/tables in Results, not just Discussion?\n"
    "5. Hallucination check - Do specific values (numbers, gene names, accession IDs, EC numbers, "
    "species names, etc.) actually appear in the paper?\n\n"
    "### For EACH field, determine:\n"
    "- SUPPORTED: The value is explicitly stated or directly inferable from the paper.\n"
    "- UNSUPPORTED: The value CANNOT be found in or inferred from the paper (likely hallucination).\n"
    "- UNCERTAIN: Partially related content exists, but the exact value is not clearly supported.\n\n"
    "Be strict: if a specific number/ID is not in the paper, mark UNSUPPORTED.\n"
    "Call the verify_all_genes function with your verification results for ALL genes at once."
)

# ─── 一次性验证所有基因的 Tool 定义 ──────────────────────────────────────────────
VERIFY_ALL_TOOL = {
    "type": "function",
    "function": {
        "name": "verify_all_genes",
        "description": (
            "Submit verification results for ALL genes at once. "
            "For each gene, provide verdicts for each non-NA field."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "gene_verdicts": {
                    "type": "array",
                    "description": "Verification results grouped by gene.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "Gene_Name": {
                                "type": "string",
                                "description": "The gene name being verified."
                            },
                            "field_verdicts": {
                                "type": "array",
                                "description": "Verification results for each field of this gene.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "field_name": {
                                            "type": "string",
                                            "description": "The field name being verified."
                                        },
                                        "verdict": {
                                            "type": "string",
                                            "enum": ["SUPPORTED", "UNSUPPORTED", "UNCERTAIN"],
                                            "description": "Verification verdict."
                                        },
                                        "reason": {
                                            "type": "string",
                                            "description": "Brief explanation for the verdict."
                                        }
                                    },
                                    "required": ["field_name", "verdict", "reason"]
                                }
                            }
                        },
                        "required": ["Gene_Name", "field_verdicts"]
                    }
                }
            },
            "required": ["gene_verdicts"]
        }
    }
}


# ═══════════════════════════════════════════════════════════════════════════════════
#  辅助函数
# ═══════════════════════════════════════════════════════════════════════════════════

def extract_non_na_fields(gene_dict):
    """提取基因字典中所有非 NA 的字段。"""
    fields = {}
    for key, value in gene_dict.items():
        if value is None:
            continue
        if isinstance(value, str) and value.strip().upper() == "NA":
            continue
        if isinstance(value, list):
            filtered = [v for v in value if not (isinstance(v, str) and v.strip().upper() == "NA")]
            if filtered:
                fields[key] = filtered
        else:
            fields[key] = value
    return fields


def resolve_test_files(files):
    """根据 TEST_INDEX 环境变量筛选测试文件。"""
    test_index = os.getenv("TEST_INDEX", "1")
    if test_index.isdigit():
        idx = int(test_index) - 1
        if 0 <= idx < len(files):
            print(f"  🧪 测试模式: 仅验证第 {idx + 1} 个文件 → {files[idx]}")
            return [files[idx]]
        else:
            print(f"  ❌ 编号 {idx + 1} 超出范围 (共 {len(files)} 个文件)")
            return []
    target = test_index if test_index.endswith(".md") else test_index + ".md"
    matched = [f for f in files if f == target]
    if matched:
        print(f"  🧪 测试模式: 按文件名匹配 → {matched[0]}")
        return matched
    matched = [f for f in files if test_index in f]
    if matched:
        print(f"  🧪 测试模式: 模糊匹配 → {matched[0]}")
        return [matched[0]]
    print(f"  ❌ 未找到匹配 '{test_index}' 的文件 (共 {len(files)} 个文件)")
    return []


def get_file_pairs():
    """自动配对 md/{name}.md -> reports/{dirname}/extraction.json"""
    pairs = []
    if not os.path.exists(MD_DIR) or not os.path.exists(REPORTS_DIR):
        return pairs
    md_files = sorted([f for f in os.listdir(MD_DIR) if f.endswith(".md")])
    if os.getenv("TEST_MODE") == "1":
        md_files = resolve_test_files(md_files)
        if not md_files:
            return pairs
    for md_file in md_files:
        stem = os.path.splitext(md_file)[0]
        dirname = stem_to_dirname(stem)
        md_path = os.path.join(MD_DIR, md_file)
        json_path = os.path.join(REPORTS_DIR, dirname, "extraction.json")
        if os.path.exists(json_path):
            pairs.append((md_path, json_path, stem))
        else:
            print(f"  ⚠️  找不到提取结果: {json_path}，跳过 {md_file}")
    return pairs


# ═══════════════════════════════════════════════════════════════════════════════════
#  核心验证逻辑：一次 API 调用验证所有基因
# ═══════════════════════════════════════════════════════════════════════════════════

def _call_verify_all_api(api_client, model_name, user_prompt, file_name):
    """调用 API 一次性验证所有基因，返回 (gene_verdicts_list, success)。"""
    try:
        response = api_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": VERIFY_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            tools=[VERIFY_ALL_TOOL],
            tool_choice={"type": "function", "function": {"name": "verify_all_genes"}},
            temperature=float(os.getenv("TEMPERATURE", "0")),
            max_tokens=16384,
        )

        tracker.add(response, stage="verify", file=file_name)
        message = response.choices[0].message

        if not message.tool_calls or len(message.tool_calls) == 0:
            print(f"    ⚠️  [{model_name}] 未触发 tool call")
            return [], False

        tool_call = message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        gene_verdicts = args.get("gene_verdicts", [])

        total_fields = sum(len(gv.get("field_verdicts", [])) for gv in gene_verdicts)
        print(f"    ✅ [{model_name}] 一次性验证成功: {len(gene_verdicts)} 个基因, {total_fields} 个字段")
        return gene_verdicts, True

    except json.JSONDecodeError as e:
        print(f"    ⚠️  [{model_name}] JSON 解析失败: {e}")
        return [], False
    except Exception as e:
        print(f"    ❌ [{model_name}] API 调用失败: {e}")
        return [], False


def _build_all_genes_text(all_genes_with_info):
    """构建所有基因的验证文本。"""
    parts = []
    for i, (gene_data, category) in enumerate(all_genes_with_info, 1):
        gene_name = gene_data.get("Gene_Name", f"Gene_{i}")
        non_na = extract_non_na_fields(gene_data)
        if not non_na:
            continue
        fields_json = json.dumps(non_na, indent=2, ensure_ascii=False)
        parts.append(
            f"### Gene #{i}: {gene_name} (Category: {category})\n"
            f"```json\n{fields_json}\n```"
        )
    return "\n\n".join(parts)


def apply_corrections(gene_data, field_verdicts_list):
    """根据验证结果修正基因数据。"""
    corrections = []
    corrected_gene = dict(gene_data)

    # 将 field_verdicts 列表转为 dict
    verdict_map = {}
    for fv in field_verdicts_list:
        fname = fv.get("field_name", "")
        if fname:
            verdict_map[fname] = fv

    for field_name, verdict_info in verdict_map.items():
        verdict = verdict_info.get("verdict", "").upper()
        reason = verdict_info.get("reason", "")

        if verdict == "UNSUPPORTED":
            old_value = corrected_gene.get(field_name)
            corrected_gene[field_name] = "NA"
            corrections.append({
                "field": field_name,
                "old_value": old_value,
                "new_value": "NA",
                "reason": reason,
            })

    return corrected_gene, corrections


# ═══════════════════════════════════════════════════════════════════════════════════
#  对外入口
# ═══════════════════════════════════════════════════════════════════════════════════

def verify_paper(md_path, extraction_dict, gene_dict, stem):
    """验证单篇论文的所有基因（一次 API 调用）。

    Args:
        md_path: MD 文件路径
        extraction_dict: 提取结果 dict（含 Common_Genes / Pathway_Genes / Regulation_Genes）
        gene_dict: 基因分类字典 {"Gene_Name": "category"}
        stem: 文件名 stem

    Returns:
        verification_report dict 或 None
    """
    verified_json_path = os.path.join(FINAL_JSON_DIR, f"{stem}_nutri_plant_verified.json")
    if os.path.exists(verified_json_path) and os.getenv("FORCE_RERUN") != "1":
        print(f"\n  ⏭️  已验证，跳过: {stem}  (设置 FORCE_RERUN=1 强制重跑)")
        return None

    print(f"\n{'='*60}")
    print(f"📄 验证文件: {stem}")
    print(f"{'='*60}")

    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    original_len = len(md_content)
    md_content = preprocess_md(md_content)
    print(f"  📏 文本预处理: {original_len:,} -> {len(md_content):,} 字符 (节省 {original_len - len(md_content):,})")

    # 收集所有基因 + 来源分组
    GENE_ARRAY_KEYS = ("Common_Genes", "Pathway_Genes", "Regulation_Genes")
    CAT_MAP = {"Common_Genes": "Common", "Pathway_Genes": "Pathway", "Regulation_Genes": "Regulation"}

    all_genes_with_info = []  # [(gene_data, category, arr_key, idx_in_arr)]
    for arr_key in GENE_ARRAY_KEYS:
        arr = extraction_dict.get(arr_key, [])
        if isinstance(arr, str):
            try:
                arr = json.loads(arr)
            except json.JSONDecodeError:
                arr = []
        if isinstance(arr, list):
            for idx, g in enumerate(arr):
                if isinstance(g, dict):
                    cat = CAT_MAP.get(arr_key, "Common")
                    all_genes_with_info.append((g, cat, arr_key, idx))

    if not all_genes_with_info:
        print("  ⚠️  没有基因需要验证")
        return None

    print(f"  🧬 待验证基因: {len(all_genes_with_info)} 个")

    # 构建验证 prompt
    genes_text = _build_all_genes_text([(g, cat) for g, cat, _, _ in all_genes_with_info])
    user_prompt = (
        f"## 论文原文 (Markdown)\n\n{md_content}\n\n"
        f"---\n\n"
        f"## 待验证的所有基因字段\n\n{genes_text}\n\n"
        f"请对每个基因的每个字段逐一验证，给出 SUPPORTED/UNSUPPORTED/UNCERTAIN 判定和理由。"
    )

    # 调用 API
    gene_verdicts, success = _call_verify_all_api(client, MODEL, user_prompt, stem)

    if not success and fallback_client:
        print(f"    🔄 主 API 验证失败，切换到 Fallback ({FALLBACK_MODEL})...")
        gene_verdicts, success = _call_verify_all_api(fallback_client, FALLBACK_MODEL, user_prompt, stem)

    if not success:
        print(f"    ⚠️  所有 API 均验证失败: {stem}")
        return None

    # 按基因名匹配验证结果
    verdict_by_name = {}
    for gv in gene_verdicts:
        gname = gv.get("Gene_Name", "")
        if gname:
            verdict_by_name[gname] = gv.get("field_verdicts", [])

    # 应用修正并构建报告
    file_report = {
        "file": stem,
        "md_path": md_path,
        "timestamp": datetime.now().isoformat(),
        "genes": [],
        "summary": {
            "total_fields": 0,
            "supported": 0,
            "unsupported": 0,
            "uncertain": 0,
            "total_corrections": 0,
        },
    }

    # 用于回写修正后的基因到 extraction_dict
    corrected_arrays = {k: list(extraction_dict.get(k, [])) for k in GENE_ARRAY_KEYS}
    # 确保是可变列表
    for k in GENE_ARRAY_KEYS:
        if isinstance(corrected_arrays[k], str):
            try:
                corrected_arrays[k] = json.loads(corrected_arrays[k])
            except json.JSONDecodeError:
                corrected_arrays[k] = []

    for gene_data, cat, arr_key, idx_in_arr in all_genes_with_info:
        gene_name = gene_data.get("Gene_Name", "Unknown")
        field_verdicts = verdict_by_name.get(gene_name, [])

        corrected_gene, corrections = apply_corrections(gene_data, field_verdicts)

        # 回写到对应数组
        if idx_in_arr < len(corrected_arrays[arr_key]):
            corrected_arrays[arr_key][idx_in_arr] = corrected_gene

        # 统计
        gene_stats = {"supported": 0, "unsupported": 0, "uncertain": 0}
        for fv in field_verdicts:
            v = fv.get("verdict", "").upper()
            if v == "SUPPORTED":
                gene_stats["supported"] += 1
            elif v == "UNSUPPORTED":
                gene_stats["unsupported"] += 1
            elif v == "UNCERTAIN":
                gene_stats["uncertain"] += 1

        total = gene_stats["supported"] + gene_stats["unsupported"] + gene_stats["uncertain"]

        print(f"\n  🧬 {gene_name} ({cat}):")
        print(f"     ✅ SUPPORTED:   {gene_stats['supported']}")
        print(f"     ❓ UNCERTAIN:   {gene_stats['uncertain']}")
        print(f"     ❌ UNSUPPORTED: {gene_stats['unsupported']}")
        if corrections:
            print(f"     🔧 已修正 {len(corrections)} 个字段")
            for c in corrections[:3]:  # 只打印前 3 个
                old_val = str(c["old_value"])[:60]
                print(f"        - {c['field']}: \"{old_val}\" -> \"NA\"")

        # 构建验证结果 dict（兼容旧格式）
        verification_dict = {}
        for fv in field_verdicts:
            fname = fv.get("field_name", "")
            if fname:
                verification_dict[fname] = {
                    "verdict": fv.get("verdict", "UNCERTAIN"),
                    "reason": fv.get("reason", ""),
                }

        file_report["genes"].append({
            "gene_name": gene_name,
            "category": cat,
            "verification": verification_dict,
            "corrections": corrections,
            "stats": gene_stats,
        })

        file_report["summary"]["total_fields"] += total
        file_report["summary"]["supported"] += gene_stats["supported"]
        file_report["summary"]["unsupported"] += gene_stats["unsupported"]
        file_report["summary"]["uncertain"] += gene_stats["uncertain"]
        file_report["summary"]["total_corrections"] += len(corrections)

    # 写回修正后的 JSON
    verified_data = dict(extraction_dict)
    for arr_key in GENE_ARRAY_KEYS:
        verified_data[arr_key] = corrected_arrays[arr_key]

    with open(verified_json_path, "w", encoding="utf-8") as f:
        json.dump(verified_data, f, indent=2, ensure_ascii=False)
    print(f"\n  ✅ 修正后的 JSON 已保存: {verified_json_path}")

    # 保存验证报告
    paper_dir = os.path.join(REPORTS_DIR, stem_to_dirname(stem))
    os.makedirs(paper_dir, exist_ok=True)
    report_path = os.path.join(paper_dir, "verification.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(file_report, f, indent=2, ensure_ascii=False)
    print(f"  📋 验证报告已保存: {report_path}")

    # 移动已处理的 MD 文件
    if os.path.exists(md_path):
        md_filename = os.path.basename(md_path)
        dest = os.path.join(PROCESSED_DIR, md_filename)
        shutil.move(md_path, dest)
        print(f"  📦 MD 已移动到: {dest}")

    return file_report


# ═══════════════════════════════════════════════════════════════════════════════════
#  旧版兼容入口 verify_file()（供旧的 run.sh verify 模式使用）
# ═══════════════════════════════════════════════════════════════════════════════════

def verify_file(md_path, json_path, stem):
    """旧版兼容入口：从文件读取 extraction_dict 后调用 verify_paper。"""
    verified_json_path = os.path.join(FINAL_JSON_DIR, f"{stem}_nutri_plant_verified.json")
    if os.path.exists(verified_json_path) and os.getenv("FORCE_RERUN") != "1":
        print(f"\n  ⏭️  已验证，跳过: {stem}  (设置 FORCE_RERUN=1 强制重跑)")
        return None

    with open(json_path, "r", encoding="utf-8") as f:
        extraction_dict = json.load(f)

    # 兼容旧版 JSON 结构
    if "CropNutrientMetabolismGeneExtraction" in extraction_dict:
        extraction_dict = extraction_dict["CropNutrientMetabolismGeneExtraction"]

    # 从 extraction 重建 gene_dict
    gene_dict = {}
    for arr_key, cat in [("Common_Genes", "Common"), ("Pathway_Genes", "Pathway"), ("Regulation_Genes", "Regulation")]:
        for g in extraction_dict.get(arr_key, []):
            if isinstance(g, dict):
                gname = g.get("Gene_Name", "")
                if gname:
                    gene_dict[gname] = cat

    # 兼容旧版单数组 "Genes"
    if not gene_dict and "Genes" in extraction_dict:
        genes = extraction_dict["Genes"]
        if isinstance(genes, list):
            # 旧版没有分类，全部放 Common
            extraction_dict["Common_Genes"] = genes
            extraction_dict["Pathway_Genes"] = []
            extraction_dict["Regulation_Genes"] = []
            for g in genes:
                if isinstance(g, dict):
                    gene_dict[g.get("Gene_Name", "")] = "Common"

    return verify_paper(md_path, extraction_dict, gene_dict, stem)


def print_summary(all_reports):
    """打印所有文件的汇总。"""
    print(f"\n{'='*60}")
    print(f"📊 总体验证汇总")
    print(f"{'='*60}")

    total_files = len(all_reports)
    total_fields = sum(r["summary"]["total_fields"] for r in all_reports)
    total_supported = sum(r["summary"]["supported"] for r in all_reports)
    total_unsupported = sum(r["summary"]["unsupported"] for r in all_reports)
    total_uncertain = sum(r["summary"]["uncertain"] for r in all_reports)
    total_corrections = sum(r["summary"]["total_corrections"] for r in all_reports)

    print(f"  验证文件数: {total_files}")
    print(f"  验证字段数: {total_fields}")
    print(f"  ✅ SUPPORTED:   {total_supported}")
    print(f"  ❓ UNCERTAIN:   {total_uncertain}")
    print(f"  ❌ UNSUPPORTED: {total_unsupported}")
    print(f"  🔧 总修正数:    {total_corrections}")

    if total_fields > 0:
        accuracy = total_supported / total_fields * 100
        print(f"  📈 忠实度:      {accuracy:.1f}%")


def main():
    """旧版独立运行入口。"""
    print("🚀 开始验证 JSON 输出的忠实度...\n")

    pairs = get_file_pairs()
    if not pairs:
        print("❌ 未找到可验证的文件对。")
        return

    print(f"📂 找到 {len(pairs)} 对待验证文件")

    all_reports = []
    for md_path, json_path, stem in pairs:
        report = verify_file(md_path, json_path, stem)
        if report:
            all_reports.append(report)

    if all_reports:
        print_summary(all_reports)

    tracker.print_summary()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tracker.save_report(os.path.join(TOKEN_USAGE_DIR, f"verify-{timestamp}.json"))
    print("\n✅ 验证完成！")


if __name__ == "__main__":
    main()
