"""
verify_response.py
验证 LLM 生成的 JSON 是否忠实于 MD 原文，检测幻觉并自动修正。

流程:
    1. 读取 MD 原文 + 对应 JSON 输出
    2. 调用 LLM API（function_calling）逐基因验证每个字段
    3. 将 UNSUPPORTED 的字段修正为 "NA"
    4. 保存修正后的 JSON 和验证报告

改进点:
    - 使用 function_calling 保证验证结果一定是合法 JSON
    - 去除 12000 字符截断，发送完整论文原文
    - References 引用列表已通过 strip_references 预处理去除
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
    """将 MD 文件名 stem 转为 reports 子目录名（GitHub 命名规范）。"""
    if stem.startswith("MinerU_markdown_"):
        stem = stem[len("MinerU_markdown_"):]
    stem = stem.replace("_(1)", "")
    stem = stem.replace("_", "-")
    return stem

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

# Fallback 客户端（DeepSeek）：当主 API 因危险词被拦截时自动切换
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
    "Your task: Given a scientific paper (Markdown) and a set of extracted JSON fields for ONE gene, "
    "verify whether EACH field value is faithfully supported by the original paper.\n\n"
    "### Verification criteria:\n"
    "1. Core gene validity - Was this gene directly tested in the Results section "
    "(knockout/knockdown/OE/CRISPR/enzyme assay), or only mentioned in Intro/Discussion?\n"
    "2. Trait validity - Is the gene linked to a final nutrient product, not just a generic trait?\n"
    "3. Directionality consistency - Do intermediate metabolite changes match the final product change?\n"
    "4. Evidence alignment - Are claims backed by figures/tables in Results, not just Discussion speculation?\n"
    "5. Hallucination check - Do specific values (numbers, gene names, accession IDs, EC numbers, "
    "species names, etc.) actually appear in the paper?\n\n"
    "### For EACH field, determine:\n"
    "- SUPPORTED: The value is explicitly stated or directly inferable from the paper.\n"
    "- UNSUPPORTED: The value CANNOT be found in or inferred from the paper (likely hallucination).\n"
    "- UNCERTAIN: Partially related content exists, but the exact value is not clearly supported.\n\n"
    "Be strict: if a specific number/ID is not in the paper, mark UNSUPPORTED.\n"
    "Call the verify_gene_fields function with your verification results."
)

# ─── Function calling tool 定义 ─────────────────────────────────────────────────
VERIFY_TOOL = {
    "type": "function",
    "function": {
        "name": "verify_gene_fields",
        "description": "Submit verification results for each field of a gene extraction. "
                       "Each field should have a verdict (SUPPORTED/UNSUPPORTED/UNCERTAIN) and a reason.",
        "parameters": {
            "type": "object",
            "properties": {
                "field_verdicts": {
                    "type": "array",
                    "description": "List of verification results, one per field.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field_name": {
                                "type": "string",
                                "description": "The field name being verified (e.g., Gene_Name, EC_Number)."
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
            "required": ["field_verdicts"]
        }
    }
}


def resolve_test_files(files):
    """根据 TEST_INDEX 环境变量筛选测试文件，支持编号和文件名。"""
    test_index = os.getenv("TEST_INDEX", "1")

    # 纯数字 → 按编号
    if test_index.isdigit():
        idx = int(test_index) - 1
        if 0 <= idx < len(files):
            print(f"  🧪 测试模式: 仅验证第 {idx + 1} 个文件 → {files[idx]}")
            return [files[idx]]
        else:
            print(f"  ❌ 编号 {idx + 1} 超出范围 (共 {len(files)} 个文件)")
            return []

    # 非数字 → 按文件名匹配
    target = test_index if test_index.endswith(".md") else test_index + ".md"
    matched = [f for f in files if f == target]
    if matched:
        print(f"  🧪 测试模式: 按文件名匹配 → {matched[0]}")
        return matched

    # 模糊匹配：文件名包含关键词
    matched = [f for f in files if test_index in f]
    if matched:
        if len(matched) == 1:
            print(f"  🧪 测试模式: 模糊匹配 → {matched[0]}")
        else:
            print(f"  🧪 测试模式: 模糊匹配到 {len(matched)} 个文件，取第一个 → {matched[0]}")
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


def extract_non_na_fields(gene_dict):
    """提取基因字典中所有非 NA 的字段"""
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


def _call_verify_api(api_client, model_name, user_prompt, gene_name):
    """调用指定 API 客户端进行验证，返回 (result_dict, success) 元组。"""
    try:
        response = api_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": VERIFY_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            tools=[VERIFY_TOOL],
            tool_choice={"type": "function", "function": {"name": "verify_gene_fields"}},
            temperature=float(os.getenv("TEMPERATURE", "0")),
        )

        tracker.add(response, stage="verify", file=gene_name, gene=gene_name)

        message = response.choices[0].message

        has_tool_calls = message.tool_calls and len(message.tool_calls) > 0
        has_content = message.content and message.content.strip()

        if not has_tool_calls and not has_content:
            print(f"    ⚠️  [{model_name}] API 返回空内容")
            return {}, False

        if has_tool_calls:
            tool_call = message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            field_verdicts = args.get("field_verdicts", [])

            result = {}
            for item in field_verdicts:
                fname = item.get("field_name", "")
                result[fname] = {
                    "verdict": item.get("verdict", "UNCERTAIN"),
                    "reason": item.get("reason", "")
                }
            print(f"    ✅ [{model_name}] Function calling 验证成功 ({len(result)} 个字段)")
            return result, True
        else:
            print(f"    ⚠️  [{model_name}] Function calling 未触发，回退到正则提取")
            raw = message.content or ""
            result = _fallback_parse_verification(raw)
            return result, bool(result)

    except json.JSONDecodeError as e:
        print(f"    ⚠️  [{model_name}] JSON 解析失败: {e}")
        return {}, False
    except Exception as e:
        print(f"    ❌ [{model_name}] API 调用失败: {e}")
        return {}, False


def verify_gene_via_api(md_content, gene_data, gene_index):
    """调用 LLM API (function_calling) 验证单个基因的所有非 NA 字段，支持 fallback"""
    non_na_fields = extract_non_na_fields(gene_data)

    if not non_na_fields:
        return {}

    gene_name = gene_data.get("Gene_Name", f"Gene_{gene_index}")
    print(f"  🔍 验证基因 [{gene_index}]: {gene_name} ({len(non_na_fields)} 个字段)...")

    fields_text = json.dumps(non_na_fields, indent=2, ensure_ascii=False)

    user_prompt = (
        f"## 论文原文 (Markdown)\n\n{md_content}\n\n"
        f"---\n\n"
        f"## 待验证的基因字段 (Gene #{gene_index}: {gene_name})\n\n"
        f"```json\n{fields_text}\n```\n\n"
        f"请逐字段验证，对每个字段给出 SUPPORTED/UNSUPPORTED/UNCERTAIN 判定和理由。"
    )

    # ── 第一次尝试：主 API ─────────────────────────────────────────────────
    result, success = _call_verify_api(client, MODEL, user_prompt, gene_name)

    # ── Fallback：如果主 API 失败且 DeepSeek fallback 可用 ─────────────────
    if not success and fallback_client:
        print(f"    🔄 主 API 验证失败，切换到 Fallback ({FALLBACK_MODEL})...")
        result, success = _call_verify_api(fallback_client, FALLBACK_MODEL, user_prompt, gene_name)

    if not success:
        print(f"    ⚠️  所有 API 均验证失败: {gene_name}")

    return result


def _fallback_parse_verification(raw):
    """回退：从文本中提取验证 JSON"""
    code_match = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
    if code_match:
        json_str = code_match.group(1)
    else:
        brace_match = re.search(r"(\{.*\})", raw, re.DOTALL)
        json_str = brace_match.group(1) if brace_match else raw

    try:
        result = json.loads(json_str)
        return result
    except json.JSONDecodeError:
        print(f"    ⚠️  Fallback JSON 解析也失败")
        return {}


def apply_corrections(gene_data, verification_result):
    """根据验证结果修正基因数据，将 UNSUPPORTED 的字段改为 'NA'"""
    corrections = []
    corrected_gene = dict(gene_data)

    for field_name, verdict_info in verification_result.items():
        if not isinstance(verdict_info, dict):
            continue
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


def verify_file(md_path, json_path, stem):
    """验证一对 md + json 文件"""
    # 增量处理：如果 verified JSON 已存在且未设置 FORCE_RERUN，跳过
    verified_json_path = os.path.join(FINAL_JSON_DIR, f"{stem}_nutri_plant_verified.json")
    if os.path.exists(verified_json_path) and os.getenv("FORCE_RERUN") != "1":
        print(f"\n  ⏭️  已验证，跳过: {stem}  (设置 FORCE_RERUN=1 强制重跑)")
        return None

    print(f"\n{'='*60}")
    print(f"📄 验证文件: {stem}")
    print(f"   MD:   {md_path}")
    print(f"   JSON: {json_path}")
    print(f"{'='*60}")

    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    # 文本预处理：去除图片、引用列表、致谢等无用内容，减少 token 消耗
    original_len = len(md_content)
    md_content = preprocess_md(md_content)
    print(f"  📏 文本预处理: {original_len:,} -> {len(md_content):,} 字符 (节省 {original_len - len(md_content):,})")

    with open(json_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    if isinstance(json_data, dict):
        if "CropNutrientMetabolismGeneExtraction" in json_data:
            root = json_data["CropNutrientMetabolismGeneExtraction"]
        else:
            root = json_data

        # ── 适配新版三数组结构 和 旧版 Genes 单数组结构 ──
        GENE_ARRAY_KEYS = ("Common_Genes", "Pathway_Genes", "Regulation_Genes")
        has_multi = any(root.get(k) is not None for k in GENE_ARRAY_KEYS)

        if has_multi:
            # 新版三数组：收集所有基因，记录来源分组
            genes = []
            gene_source_map = []  # 记录每个基因属于哪个数组
            for arr_key in GENE_ARRAY_KEYS:
                arr = root.get(arr_key, [])
                if isinstance(arr, str):
                    try:
                        arr = json.loads(arr)
                    except json.JSONDecodeError:
                        arr = []
                if isinstance(arr, list):
                    for g in arr:
                        genes.append(g)
                        gene_source_map.append(arr_key)
            top_level_fields = {k: v for k, v in root.items() if k not in GENE_ARRAY_KEYS}
            print(f"  📊 三数组模式: Common={len(root.get('Common_Genes', []))}, "
                  f"Pathway={len(root.get('Pathway_Genes', []))}, "
                  f"Regulation={len(root.get('Regulation_Genes', []))}")
        else:
            # 旧版单数组
            genes = root.get("Genes", [])
            gene_source_map = ["Genes"] * len(genes) if isinstance(genes, list) else []
            if isinstance(genes, str):
                print(f"  ⚠️  Genes 字段是字符串而非列表，尝试解析...")
                try:
                    genes = json.loads(genes)
                    gene_source_map = ["Genes"] * len(genes)
                    print(f"  ✅ 解析成功: {len(genes)} 个基因")
                except json.JSONDecodeError as e:
                    print(f"  ❌ Genes 字符串解析失败（可能被截断）: {e}")
                    print(f"  ⏭️  跳过此文件，需要重新提取")
                    return None
            top_level_fields = {k: v for k, v in root.items() if k != "Genes"}
    else:
        print("  ❌ JSON 格式不符合预期，跳过")
        return None

    print(f"  📊 论文级字段: {len(top_level_fields)} 个")
    print(f"  🧬 基因数量: {len(genes)} 个")

    file_report = {
        "file": stem,
        "md_path": md_path,
        "json_path": json_path,
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

    all_corrected_genes = []

    for i, gene in enumerate(genes):
        gene_name = gene.get("Gene_Name", f"Gene_{i}")

        verification = verify_gene_via_api(md_content, gene, i + 1)
        corrected_gene, corrections = apply_corrections(gene, verification)
        all_corrected_genes.append(corrected_gene)

        gene_stats = {"supported": 0, "unsupported": 0, "uncertain": 0}
        for field, info in verification.items():
            if isinstance(info, dict):
                v = info.get("verdict", "").upper()
                if v == "SUPPORTED":
                    gene_stats["supported"] += 1
                elif v == "UNSUPPORTED":
                    gene_stats["unsupported"] += 1
                elif v == "UNCERTAIN":
                    gene_stats["uncertain"] += 1

        total = gene_stats["supported"] + gene_stats["unsupported"] + gene_stats["uncertain"]

        print(f"\n  🧬 Gene [{i+1}] {gene_name}:")
        print(f"     ✅ SUPPORTED:   {gene_stats['supported']}")
        print(f"     ❓ UNCERTAIN:   {gene_stats['uncertain']}")
        print(f"     ❌ UNSUPPORTED: {gene_stats['unsupported']}")

        if corrections:
            print(f"     🔧 已修正 {len(corrections)} 个字段:")
            for c in corrections:
                old_val = c["old_value"]
                if isinstance(old_val, str) and len(old_val) > 60:
                    old_val = old_val[:60] + "..."
                print(f"        - {c['field']}: \"{old_val}\" -> \"NA\"")
                print(f"          原因: {c['reason']}")

        file_report["genes"].append({
            "gene_index": i + 1,
            "gene_name": gene_name,
            "verification": verification,
            "corrections": corrections,
            "stats": gene_stats,
        })

        file_report["summary"]["total_fields"] += total
        file_report["summary"]["supported"] += gene_stats["supported"]
        file_report["summary"]["unsupported"] += gene_stats["unsupported"]
        file_report["summary"]["uncertain"] += gene_stats["uncertain"]
        file_report["summary"]["total_corrections"] += len(corrections)

    # ── 将修正后的基因写回原结构 ──
    if isinstance(json_data, dict):
        if "CropNutrientMetabolismGeneExtraction" in json_data:
            target = json_data["CropNutrientMetabolismGeneExtraction"]
        else:
            target = json_data

        if has_multi:
            # 新版三数组：按 gene_source_map 分回各自数组
            rebuilt = {k: [] for k in GENE_ARRAY_KEYS}
            for corrected, src_key in zip(all_corrected_genes, gene_source_map):
                rebuilt[src_key].append(corrected)
            for arr_key in GENE_ARRAY_KEYS:
                target[arr_key] = rebuilt[arr_key]
        else:
            # 旧版单数组
            target["Genes"] = all_corrected_genes

    verified_json_path = os.path.join(FINAL_JSON_DIR, f"{stem}_nutri_plant_verified.json")
    with open(verified_json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    print(f"\n  ✅ 修正后的 JSON 已保存: {verified_json_path}")

    paper_dir = os.path.join(REPORTS_DIR, stem_to_dirname(stem))
    os.makedirs(paper_dir, exist_ok=True)
    report_path = os.path.join(paper_dir, "verification.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(file_report, f, indent=2, ensure_ascii=False)
    print(f"  📋 验证报告已保存: {report_path}")

    # ─── 移动已处理的 MD 文件到 processed 目录 ─────────────────────────────────
    if os.path.exists(md_path):
        md_filename = os.path.basename(md_path)
        dest = os.path.join(PROCESSED_DIR, md_filename)
        shutil.move(md_path, dest)
        print(f"  📦 MD 已移动到: {dest}")

    return file_report


def print_summary(all_reports):
    """打印所有文件的汇总"""
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
    """主函数"""
    print("🚀 开始验证 JSON 输出的忠实度...\n")

    pairs = get_file_pairs()

    if not pairs:
        print("❌ 未找到可验证的文件对。")
        print(f"   请确保 {MD_DIR} 中有 .md 文件，")
        print(f"   且 {REPORTS_DIR} 中有对应的 extraction.json 文件。")
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
