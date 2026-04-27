from __future__ import annotations

import json
import logging
import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

from crispr import accession2sequence as step2_acc2seq
from crispr import crispr_target as step3_crispr
from crispr import experiment_design as step4_design
from crispr import gene2accession as step1_gene2acc
from shared.llm import call_llm_sync

logger = logging.getLogger(__name__)


def _json_from_llm_text(raw: str):
    text = raw.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


class ExperimentPipeline:
    """CRISPR experiment-design pipeline orchestrator."""

    def __init__(self, work_dir: Path | None = None):
        self.work_dir = work_dir or Path(tempfile.mkdtemp(prefix="crispr_pipeline_"))

    def extract_genes_with_llm(self, answer_text: str) -> list[dict]:
        prompt = (
            "从以下文本中提取所有需要进行实验操作的基因名称和对应物种（拉丁名）。\n"
            "包括：用户明确要求生成 SOP 的基因、被建议编辑/敲除/过表达的基因。\n"
            '返回 JSON 数组格式: [{"gene": "Shrunken-2", "species": "Zea mays"}]\n'
            "基因名保持原文中的写法。如果文本未明确物种，根据上下文推断。\n"
            "如果没有找到，返回空数组 []。\n\n"
            f"文本：\n{answer_text}"
        )
        genes = _json_from_llm_text(call_llm_sync([{"role": "user", "content": prompt}], temperature=0).content)
        if not isinstance(genes, list) or not genes:
            raise ValueError("未从回答中提取到建议编辑的基因")
        return genes

    def extract_selected_genes_with_llm(self, answer_text: str, gene_names: list[str]) -> list[dict]:
        gene_list = ", ".join(gene_names)
        prompt = (
            f"以下是用户选定的基因列表：{gene_list}\n\n"
            "请根据下方文本的上下文，为每个基因确定其对应的物种（拉丁名）。\n"
            "如果文本中未提及某个基因的物种，请根据基因名前缀推断"
            "（如 Gm=Glycine max, At=Arabidopsis thaliana, Os=Oryza sativa, "
            "Sl=Solanum lycopersicum, Zm=Zea mays）。\n"
            '返回 JSON 数组格式: [{"gene": "GmFAD2", "species": "Glycine max"}]\n\n'
            f"文本：\n{answer_text}"
        )
        genes = _json_from_llm_text(call_llm_sync([{"role": "user", "content": prompt}], temperature=0).content)
        if not isinstance(genes, list) or not genes:
            raise ValueError("未能为选定的基因解析物种信息")
        return genes

    def run_all_from_genes(self, genes: list[dict]) -> Generator[dict, None, None]:
        try:
            gene_names = ", ".join(gene["gene"] for gene in genes)

            yield {
                "type": "progress",
                "step": 1,
                "total": 4,
                "msg": f"正在查询 NCBI 获取 accession（{gene_names}）...",
            }
            acc_file = step1_gene2acc.run_gene2accession(genes, self.work_dir)
            yield {"type": "progress", "step": 1, "total": 4, "msg": "Accession 查询完成"}

            yield {"type": "progress", "step": 2, "total": 4, "msg": "正在从 NCBI 下载基因序列..."}
            fasta = step2_acc2seq.run_accession2sequence(acc_file, self.work_dir)
            yield {"type": "progress", "step": 2, "total": 4, "msg": "序列下载完成"}

            yield {
                "type": "progress",
                "step": 3,
                "total": 4,
                "msg": "正在设计 CRISPR 靶点（可能需要 10-30 秒）...",
            }
            targets = step3_crispr.run_crispr_target(fasta, self.work_dir)
            yield {"type": "progress", "step": 3, "total": 4, "msg": "CRISPR 靶点设计完成"}

            yield {"type": "progress", "step": 4, "total": 4, "msg": "正在生成实验方案 SOP..."}
            sops = step4_design.run_experiment_design(targets, self.work_dir, acc_file)
            yield {"type": "progress", "step": 4, "total": 4, "msg": "实验方案生成完成"}
            yield {"type": "result", "sops": sops}
        except Exception as exc:
            logger.exception("实验方案 pipeline 执行出错")
            yield {"type": "error", "msg": str(exc)}

    def cleanup(self) -> None:
        shutil.rmtree(self.work_dir, ignore_errors=True)


__all__ = ["ExperimentPipeline"]
