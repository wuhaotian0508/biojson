"""
verify_response.py  (v3 — 使用 ToolRegistry.call_tool 硬编码调用)

验证模块：通过 load_skill() 加载 verify_all_genes tool，
代码硬编码 registry.call_tool("verify_all_genes") 一次 API 调用验证所有基因。

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
from tool_registry import load_skill, ToolRegistry

load_dotenv()

# ─── 配置 ────────────────────────────────────────────────────────────────────────
BASE_DIR = os.getenv("BASE_DIR", "/data/haotianwu/biojson")
MD_DIR = os.getenv("MD_DIR", os.path.join(BASE_DIR, "md"))
REPORTS_DIR = os.getenv("REPORTS_DIR", os.path.join(BASE_DIR, "reports"))
FINAL_JSON_DIR = os.getenv("JSON_DIR", os.path.join(BASE_DIR, "json"))
TOKEN_USAGE_DIR = os.getenv("TOKEN_USAGE_DIR", os.path.join(BASE_DIR, "token-usage"))
PROCESSED_DIR = os.getenv("PROCESSED_DIR", os.path.join(MD_DIR, "processed"))
SKILLS_DIR = os.path.join(BASE_DIR, "skills")
EXTRACTION_SKILL_DIR = os.path.join(SKILLS_DIR, "biojson-extraction")

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

# ─── 分批验证参数 ───────────────────────────────────────────────────────────────
VERIFY_BATCH_SIZE = int(os.getenv("VERIFY_BATCH_SIZE", "3"))  # 每批验证基因数，防止 context 超长

# ─── 验证 Prompt ────────────────────────────────────────────────────────────────
VERIFY_SYSTEM_PROMPT = """You are a rigorous academic verification assistant specializing in plant molecular biology and metabolic biochemistry.

Your task: Given a scientific paper (Markdown) and extracted JSON fields for ALL genes, verify whether EACH field value is faithfully supported by the original paper.

### Verification criteria:
1. Core gene validity - Was this gene directly tested in the Results section?
2. Trait validity - Is the gene linked to a final nutrient product, not just a generic trait?
3. Directionality consistency - Do intermediate metabolite changes match the final product change?
4. Evidence alignment - Are claims backed by figures/tables in Results, not just Discussion?
5. Hallucination check - Do specific values (numbers, gene names, accession IDs, EC numbers, species names, etc.) actually appear in the paper?

### For EACH field, determine:
- SUPPORTED: The value is explicitly stated or directly inferable from the paper.
- UNSUPPORTED: The value CANNOT be found in or inferred from the paper (likely hallucination).
- UNCERTAIN: Partially related content exists, but the exact value is not clearly supported.

Be strict: if a specific number/ID is not in the paper, mark UNSUPPORTED.
Call the verify_all_genes function with your verification results for ALL genes at once."""


# ═══════════════════════════════════════════════════════════════════════════════════
#  加载验证 registry（只取 verify_all_genes tool）
# ═══════════════════════════════════════════════════════════════════════════════════

def _load_verify_registry():
    """从 SKILL.md 加载技能，只保留 verify_all_genes tool。"""
    full_registry = load_skill(EXTRACTION_SKILL_DIR, schema_base_dir=BASE_DIR)

    verify_registry = ToolRegistry()
    for name, tool_info in full_registry._tools.items():
        if name == "verify_all_genes":
            verify_registry.register(name, tool_info["schema"], tool_info["handler"])

    return verify_registry


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
            print(f"  🧪 测试模式: 仅验证第 {idx + 1} 个文件 -> {files[idx]}")
            return [files[idx]]
        else:
            print(f"  ❌ 编号 {idx + 1} 超出范围 (共 {len(files)} 个文件)")
            return []
    target = test_index if test_index.endswith(".md") else test_index + ".md"
    matched = [f for f in files if f == target]
    if matched:
        print(f"  🧪 测试模式: 按文件名匹配 -> {matched[0]}")
        return matched
    matched = [f for f in files if test_index in f]
    if matched:
        print(f"  🧪 测试模式: 模糊匹配 -> {matched[0]}")
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
#  核心验证逻辑：使用 registry.call_tool 硬编码调用 verify_all_genes
# ═══════════════════════════════════════════════════════════════════════════════════

def _call_verify_api(api_client, model_name, user_prompt, file_name, registry):
    """使用 ToolRegistry.call_tool 硬编码调用 verify_all_genes。

    返回 (gene_verdicts_list, success)。
    如果 LLM 成功触发 tool call 但 field_verdicts 全为空，也返回 False 触发 fallback。
    """
    messages = [
        {"role": "system", "content": VERIFY_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    print(f"    🔵 API Call: verify_all_genes...")
    parsed_args, success = registry.call_tool(
        client=api_client,
        model=model_name,
        messages=messages,
        tool_name="verify_all_genes",
        tracker=tracker,
        stage="verify",
        file_name=file_name,
        temperature=float(os.getenv("TEMPERATURE", "0")),
        max_tokens=16384,
    )

    if not success or parsed_args is None:
        print(f"    ⚠️  [{model_name}] verify_all_genes 调用失败")
        return [], False

    gene_verdicts = registry.state.get("verify_results", [])
    total_fields = sum(len(gv.get("field_verdicts", [])) for gv in gene_verdicts)

    # 关键检查：field_verdicts 全为空 = 主 API context 超长导致空响应，触发 fallback
    if not gene_verdicts or total_fields == 0:
        print(f"    ⚠️  [{model_name}] verify 结果为空 (genes={len(gene_verdicts)}, fields=0)，触发 fallback")
        return [], False

    print(f"    ✅ [{model_name}] 验证成功: {len(gene_verdicts)} 个基因, {total_fields} 个字段")
    return gene_verdicts, True


# ═══════════════════════════════════════════════════════════════════════════════════
#  对外入口
# ═══════════════════════════════════════════════════════════════════════════════════

def verify_paper(md_path, extraction_dict, gene_dict, stem):
    """验证单篇论文的所有基因（一次 API 调用，通过 registry.call_tool）。

    Args:
        md_path: MD 文件路径
        extraction_dict: 提取结果 dict
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

    all_genes_with_info = []
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

    total_genes = len(all_genes_with_info)
    batch_size = VERIFY_BATCH_SIZE
    num_batches = (total_genes + batch_size - 1) // batch_size
    print(f"  🧬 待验证基因: {total_genes} 个，分 {num_batches} 批（每批 {batch_size} 个）")

    # ── 分批调用 API，合并所有 gene_verdicts ──────────────────────────────────
    all_gene_verdicts = []
    batch_failed = False

    for batch_idx in range(num_batches):
        start = batch_idx * batch_size
        end = min(start + batch_size, total_genes)
        batch_genes = all_genes_with_info[start:end]

        gene_names_in_batch = [g.get("Gene_Name", f"Gene_{start+i+1}") for i, (g, _, _, _) in enumerate(batch_genes)]
        print(f"\n  📦 批次 {batch_idx+1}/{num_batches}: 基因 {start+1}-{end} ({', '.join(gene_names_in_batch)})")

        genes_text = _build_all_genes_text([(g, cat) for g, cat, _, _ in batch_genes])
        user_prompt = (
            f"## 论文原文 (Markdown)\n\n{md_content}\n\n"
            f"---\n\n"
            f"## 待验证的基因字段（批次 {batch_idx+1}/{num_batches}，共 {len(batch_genes)} 个基因）\n\n{genes_text}\n\n"
            f"请对这批基因的每个字段逐一验证，给出 SUPPORTED/UNSUPPORTED/UNCERTAIN 判定和理由。"
        )

        # 主 API
        registry = _load_verify_registry()
        batch_verdicts, success = _call_verify_api(client, MODEL, user_prompt, f"{stem}_batch{batch_idx+1}", registry)

        # fallback
        if not success and fallback_client:
            print(f"    🔄 主 API 失败，切换到 Fallback ({FALLBACK_MODEL})...")
            registry_fb = _load_verify_registry()
            batch_verdicts, success = _call_verify_api(fallback_client, FALLBACK_MODEL, user_prompt, f"{stem}_batch{batch_idx+1}", registry_fb)

        if not success:
            print(f"    ⚠️  批次 {batch_idx+1} 所有 API 均失败，跳过该批次")
            batch_failed = True
            continue

        all_gene_verdicts.extend(batch_verdicts)

    if not all_gene_verdicts:
        print(f"    ⚠️  所有批次均验证失败: {stem}")
        return None

    if batch_failed:
        print(f"  ⚠️  部分批次失败，继续处理已获得的验证结果")

    gene_verdicts = all_gene_verdicts
    success = True

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

    corrected_arrays = {k: list(extraction_dict.get(k, [])) for k in GENE_ARRAY_KEYS}
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

        if idx_in_arr < len(corrected_arrays[arr_key]):
            corrected_arrays[arr_key][idx_in_arr] = corrected_gene

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
            for c in corrections[:3]:
                old_val = str(c["old_value"])[:60]
                print(f"        - {c['field']}: \"{old_val}\" -> \"NA\"")

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
#  旧版兼容入口
# ═══════════════════════════════════════════════════════════════════════════════════

def verify_file(md_path, json_path, stem):
    """旧版兼容入口：从文件读取 extraction_dict 后调用 verify_paper。"""
    verified_json_path = os.path.join(FINAL_JSON_DIR, f"{stem}_nutri_plant_verified.json")
    if os.path.exists(verified_json_path) and os.getenv("FORCE_RERUN") != "1":
        print(f"\n  ⏭️  已验证，跳过: {stem}  (设置 FORCE_RERUN=1 强制重跑)")
        return None

    with open(json_path, "r", encoding="utf-8") as f:
        extraction_dict = json.load(f)

    if "CropNutrientMetabolismGeneExtraction" in extraction_dict:
        extraction_dict = extraction_dict["CropNutrientMetabolismGeneExtraction"]

    gene_dict = {}
    for arr_key, cat in [("Common_Genes", "Common"), ("Pathway_Genes", "Pathway"), ("Regulation_Genes", "Regulation")]:
        for g in extraction_dict.get(arr_key, []):
            if isinstance(g, dict):
                gname = g.get("Gene_Name", "")
                if gname:
                    gene_dict[gname] = cat

    if not gene_dict and "Genes" in extraction_dict:
        genes = extraction_dict["Genes"]
        if isinstance(genes, list):
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
