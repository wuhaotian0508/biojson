"""
verify.py — Gene verification with inline FC + dynamic batching.

Dynamic batching strategy (per 10 genes):
    < 10 genes  → 1 batch
    10-19 genes → 2 batches
    20-29 genes → 3 batches

[PR 改动 by 学长 muskliu - 2026-03-29]
- 导入改为使用 utils.py 中的共享工具函数（GENE_ARRAY_KEYS, ensure_list, safe_parse_json, stem_to_dirname）
  原来是从 extract.py 导入 stem_to_dirname, _safe_parse_json, _message_to_dict（跨模块耦合）
- preprocess_md → preprocess_md_for_llm（text_utils 中重命名）
- 拆分 verify_paper() 为 4 个子函数，逻辑更清晰：
  _collect_genes_for_verification() — 收集所有 gene 信息
  _run_batch_verification() — 执行分批 API 调用
  _build_verification_report() — 构建验证报告 + 应用修正
  _save_verification_results() — 保存文件
- 删除冗余的 docstring 注释
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

from .config import (
    MODEL, FALLBACK_MODEL, OUTPUT_DIR, REPORTS_DIR, PROCESSED_DIR,
    get_openai_client, get_fallback_client,
)
from .text_utils import preprocess_md_for_llm
from .token_tracker import TokenTracker
from .utils import (
    GENE_ARRAY_KEYS, ensure_list, safe_parse_json, stem_to_dirname,
)


# ─── Verify FC schema (inline) ──────────────────────────────────────────────

VERIFY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "verify_all_genes",
        "description": "Submit verification results for ALL genes at once. For each gene, provide verdicts for each non-NA field.",
        "parameters": {
            "type": "object",
            "properties": {
                "gene_verdicts": {
                    "type": "array",
                    "description": "Verification results grouped by gene.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "Gene_Name": {"type": "string", "description": "The gene name being verified."},
                            "field_verdicts": {
                                "type": "array",
                                "description": "Verification results for each field of this gene.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "field_name": {"type": "string", "description": "The field name being verified."},
                                        "verdict": {
                                            "type": "string",
                                            "enum": ["SUPPORTED", "UNSUPPORTED", "UNCERTAIN"],
                                            "description": "Verification verdict.",
                                        },
                                        "reason": {"type": "string", "description": "Brief explanation for the verdict."},
                                    },
                                    "required": ["field_name", "verdict", "reason"],
                                },
                            },
                        },
                        "required": ["Gene_Name", "field_verdicts"],
                    },
                },
            },
            "required": ["gene_verdicts"],
        },
    },
}

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


# ─── Helper functions ────────────────────────────────────────────────────────

def _extract_non_na_fields(gene_dict: dict) -> dict:
    """Extract all non-NA fields from a gene dict."""
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


def _build_genes_text(genes_with_info: list) -> str:
    """Build verification text for a batch of genes."""
    parts = []
    for i, (gene_data, category) in enumerate(genes_with_info, 1):
        gene_name = gene_data.get("Gene_Name", f"Gene_{i}")
        non_na = _extract_non_na_fields(gene_data)
        if not non_na:
            continue
        fields_json = json.dumps(non_na, indent=2, ensure_ascii=False)
        parts.append(
            f"### Gene #{i}: {gene_name} (Category: {category})\n"
            f"```json\n{fields_json}\n```"
        )
    return "\n\n".join(parts)


def _apply_corrections(gene_data: dict, field_verdicts_list: list) -> Tuple[dict, list]:
    """Apply UNSUPPORTED → NA corrections."""
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


def _compute_batches(total_genes: int) -> List[Tuple[int, int]]:
    """Dynamic batching: returns list of (start, end) tuples."""
    if total_genes < 10:
        return [(0, total_genes)]

    num_batches = (total_genes // 10) + 1
    batch_size = (total_genes + num_batches - 1) // num_batches
    batches = []
    for start in range(0, total_genes, batch_size):
        end = min(start + batch_size, total_genes)
        batches.append((start, end))
    return batches


def _handle_verify_all(arguments: dict) -> list:
    """Process verify_all_genes result → gene_verdicts list."""
    return ensure_list(arguments.get("gene_verdicts", []))


# ─── Core verify API call ────────────────────────────────────────────────────

def _call_verify_api(api_client, model_name: str, user_prompt: str,
                     file_name: str, tracker: TokenTracker):
    """Single batch verify API call. Returns (gene_verdicts_list, success)."""
    messages = [
        {"role": "system", "content": VERIFY_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    print(f"    🔵 API Call: verify_all_genes...")
    try:
        response = api_client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=[VERIFY_SCHEMA],
            tool_choice={"type": "function", "function": {"name": "verify_all_genes"}},
            temperature=0,
            max_tokens=16384,
        )
    except Exception as e:
        print(f"    ❌ [{model_name}] API error (verify): {e}")
        return [], False

    tracker.add(response, stage="verify", file=file_name)
    msg = response.choices[0].message

    if not msg.tool_calls:
        print(f"    ⚠️  [{model_name}] verify did not trigger tool call")
        return [], False

    tc = msg.tool_calls[0]
    parsed = safe_parse_json(tc.function.arguments, "verify")
    if parsed is None:
        return [], False

    gene_verdicts = _handle_verify_all(parsed)
    total_fields = sum(len(gv.get("field_verdicts", [])) for gv in gene_verdicts)

    if not gene_verdicts or total_fields == 0:
        print(f"    ⚠️  [{model_name}] verify result empty (genes={len(gene_verdicts)}, fields=0)")
        return [], False

    print(f"    ✅ [{model_name}] Verified: {len(gene_verdicts)} genes, {total_fields} fields")
    return gene_verdicts, True


# ═════════════════════════════════════════════════════���═════════════════════════
#  verify_paper sub-functions
# ═══════════════════════════════════════════════════════════════════════════════

def _collect_genes_for_verification(extraction_dict: dict) -> list:
    """Collect all genes with category and position info.

    Returns:
        list of (gene_data, category, arr_key, index_in_array) tuples
    """
    all_genes = []
    for arr_key, cat in GENE_ARRAY_KEYS:
        arr = ensure_list(extraction_dict.get(arr_key, []))
        for idx, g in enumerate(arr):
            if isinstance(g, dict):
                all_genes.append((g, cat, arr_key, idx))
    return all_genes


def _run_batch_verification(
    md_content: str,
    all_genes_with_info: list,
    stem: str,
    tracker: TokenTracker,
) -> list:
    """Run batched verification API calls. Returns aggregated gene_verdicts."""
    total_genes = len(all_genes_with_info)
    batches = _compute_batches(total_genes)
    print(f"  🧬 Genes to verify: {total_genes}, batches: {len(batches)}")

    client = get_openai_client()
    fallback_client = get_fallback_client()
    all_gene_verdicts = []
    batch_failed = False

    for batch_idx, (start, end) in enumerate(batches):
        batch_genes = all_genes_with_info[start:end]
        gene_names_in_batch = [g.get("Gene_Name", f"Gene_{start + i + 1}") for i, (g, _, _, _) in enumerate(batch_genes)]
        print(f"\n  📦 Batch {batch_idx + 1}/{len(batches)}: genes {start + 1}-{end} ({', '.join(gene_names_in_batch)})")

        genes_text = _build_genes_text([(g, cat) for g, cat, _, _ in batch_genes])
        user_prompt = (
            f"## Paper Text (Markdown)\n\n{md_content}\n\n"
            f"---\n\n"
            f"## Genes to Verify (batch {batch_idx + 1}/{len(batches)}, {len(batch_genes)} genes)\n\n{genes_text}\n\n"
            f"Please verify each field of each gene. Give SUPPORTED/UNSUPPORTED/UNCERTAIN verdict with reason."
        )

        batch_verdicts, success = _call_verify_api(client, MODEL, user_prompt, f"{stem}_batch{batch_idx + 1}", tracker)

        if not success and fallback_client and FALLBACK_MODEL:
            print(f"    🔄 Primary failed, switching to Fallback ({FALLBACK_MODEL})...")
            batch_verdicts, success = _call_verify_api(fallback_client, FALLBACK_MODEL, user_prompt, f"{stem}_batch{batch_idx + 1}", tracker)

        if not success:
            print(f"    ⚠️  Batch {batch_idx + 1} all APIs failed, skipping")
            batch_failed = True
            continue

        all_gene_verdicts.extend(batch_verdicts)

    if batch_failed and all_gene_verdicts:
        print(f"  ⚠️  Some batches failed, processing available results")

    return all_gene_verdicts


def _build_verification_report(
    extraction_dict: dict,
    all_genes_with_info: list,
    all_gene_verdicts: list,
    stem: str,
    md_path: Path,
) -> Tuple[dict, dict]:
    """Build verification report and apply corrections.

    Returns:
        (file_report, verified_data)
    """
    # Match verdicts to genes by name
    verdict_by_name = {}
    for gv in all_gene_verdicts:
        gname = gv.get("Gene_Name", "")
        if gname:
            verdict_by_name[gname] = gv.get("field_verdicts", [])

    file_report = {
        "file": stem,
        "md_path": str(md_path),
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

    corrected_arrays = {}
    for arr_key, _ in GENE_ARRAY_KEYS:
        corrected_arrays[arr_key] = list(ensure_list(extraction_dict.get(arr_key, [])))

    for gene_data, cat, arr_key, idx_in_arr in all_genes_with_info:
        gene_name = gene_data.get("Gene_Name", "Unknown")
        field_verdicts = verdict_by_name.get(gene_name, [])

        corrected_gene, corrections = _apply_corrections(gene_data, field_verdicts)

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
            print(f"     🔧 Corrected {len(corrections)} fields")
            for c in corrections[:3]:
                old_val = str(c["old_value"])[:60]
                print(f"        - {c['field']}: \"{old_val}\" → \"NA\"")

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

    # Build verified data
    verified_data = dict(extraction_dict)
    for arr_key, _ in GENE_ARRAY_KEYS:
        verified_data[arr_key] = corrected_arrays[arr_key]

    return file_report, verified_data


def _save_verification_results(
    verified_data: dict,
    file_report: dict,
    stem: str,
    md_path: Path,
):
    """Write verified JSON, report, and move processed MD."""
    # Write corrected verified JSON
    verified_json_path = OUTPUT_DIR / f"{stem}_nutri_plant_verified.json"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(verified_json_path, "w", encoding="utf-8") as f:
        json.dump(verified_data, f, indent=2, ensure_ascii=False)
    print(f"\n  ✅ Verified JSON saved: {verified_json_path}")

    # Save verification report
    paper_dir = REPORTS_DIR / stem_to_dirname(stem)
    paper_dir.mkdir(parents=True, exist_ok=True)
    report_path = paper_dir / "verification.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(file_report, f, indent=2, ensure_ascii=False)
    print(f"  📋 Report saved: {report_path}")

    # Move processed MD
    if md_path.exists():
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        dest = PROCESSED_DIR / md_path.name
        shutil.move(str(md_path), str(dest))
        print(f"  📦 MD moved to: {dest}")


# ═══════════════════════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════════════════════

def verify_paper(
    md_path,
    extraction_dict: dict,
    stem: str,
    tracker: TokenTracker,
) -> Optional[dict]:
    """Verify all genes in a paper with dynamic batching.

    Orchestrates: collect → batch verify → build report → save.

    Returns:
        verification_report dict, skipped sentinel, or None on failure
    """
    md_path = Path(md_path)

    # Incremental: skip if already verified
    verified_json_path = OUTPUT_DIR / f"{stem}_nutri_plant_verified.json"
    if verified_json_path.exists() and os.getenv("FORCE_RERUN") != "1":
        print(f"\n  ⏭️  Already verified, skip: {stem}  (set FORCE_RERUN=1 to re-run)")
        return {"status": "skipped", "report": None}

    print(f"\n{'=' * 60}")
    print(f"📄 Verifying: {stem}")
    print(f"{'=' * 60}")

    # Read and preprocess
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()
    original_len = len(md_content)
    md_content = preprocess_md_for_llm(md_content, tracker=tracker)
    print(f"  📏 Preprocessing: {original_len:,} → {len(md_content):,} chars (saved {original_len - len(md_content):,})")

    # 1. Collect genes
    all_genes_with_info = _collect_genes_for_verification(extraction_dict)
    if not all_genes_with_info:
        print("  ⚠️  No genes to verify")
        return None

    # 2. Batch verification
    all_gene_verdicts = _run_batch_verification(md_content, all_genes_with_info, stem, tracker)
    if not all_gene_verdicts:
        print(f"    ⚠️  All batches failed: {stem}")
        return None

    # 3. Build report + apply corrections
    file_report, verified_data = _build_verification_report(
        extraction_dict, all_genes_with_info, all_gene_verdicts, stem, md_path,
    )

    # 4. Save results
    _save_verification_results(verified_data, file_report, stem, md_path)

    return file_report
