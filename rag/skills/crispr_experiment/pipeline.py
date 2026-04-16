"""
CRISPR 实验方案自动生成 Pipeline（编排器）

功能：将 4 个独立步骤组合为完整的 pipeline，提供：
  - extract_genes_with_llm()          从 LLM 回答中提取建议编辑的基因
  - extract_selected_genes_with_llm()  为用户选定的基因名解析物种信息
  - run_all_from_genes()              执行完整 pipeline 并 yield 进度事件

4 个步骤分别对应同目录下的独立模块：
  1. gene2accession.py     — 基因名 → NCBI accession
  2. accession2sequence.py — accession → FASTA 序列
  3. crispr_target.py      — FASTA → CRISPR 靶点
  4. experiment_design.py  — 靶点 → SOP 实验方案
"""
from __future__ import annotations

import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Generator

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.llm_client import call_llm_sync

# ---- 导入 4 个 pipeline 步骤模块 ----
from . import gene2accession as step1_gene2acc
from . import accession2sequence as step2_acc2seq
from . import crispr_target as step3_crispr
from . import experiment_design as step4_design

logger = logging.getLogger(__name__)


class ExperimentPipeline:
    """
    CRISPR 实验方案生成 Pipeline 编排器。

    使用方式：
        pipeline = ExperimentPipeline()
        try:
            for event in pipeline.run_all_from_genes(genes):
                # 处理 progress / result / error 事件
                ...
        finally:
            pipeline.cleanup()
    """

    def __init__(self):
        # ---- 创建临时工作目录，所有中间文件都存放于此 ----
        self.work_dir = Path(tempfile.mkdtemp(prefix="crispr_pipeline_"))

    # ------------------------------------------------------------------
    # LLM 提取基因名 + 物种（从 LLM 回答文本中自动提取）
    # ------------------------------------------------------------------
    def extract_genes_with_llm(self, answer_text: str) -> list[dict]:
        """
        从 LLM 回答文本中提取所有被建议进行基因编辑的基因。

        使用 LLM 分析回答内容，识别出：
        - 明确建议编辑/敲除/过表达的基因（不包括仅被提及的基因）
        - 每个基因对应的物种拉丁名

        参数:
            answer_text: LLM 生成的回答全文

        返回:
            [{"gene": "GmMYB4", "species": "Glycine max"}, ...]

        异常:
            ValueError: 当未从回答中提取到任何建议编辑的基因时抛出
        """
        prompt = (
            "从以下文本中提取所有需要进行实验操作的基因名称和对应物种（拉丁名）。\n"
            "包括：用户明确要求生成 SOP 的基因、被建议编辑/敲除/过表达的基因。\n"
            '返回 JSON 数组格式: [{"gene": "Shrunken-2", "species": "Zea mays"}]\n'
            "基因名保持原文中的写法。如果文本未明确物种，根据上下文推断。\n"
            "如果没有找到，返回空数组 []。\n\n"
            f"文本：\n{answer_text}"
        )
        # messages: 发给 LLM 的消息列表（单轮对话）
        messages = [{"role": "user", "content": prompt}]

        resp = call_llm_sync(messages, temperature=0)

        # raw: LLM 返回的原始文本，可能是 JSON 或 markdown 代码块包裹的 JSON
        raw = resp.content.strip()

        # ---- 兼容 markdown code block 格式（```json ... ```） ----
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        genes = json.loads(raw.strip())
        if not isinstance(genes, list) or len(genes) == 0:
            raise ValueError("未从回答中提取到建议编辑的基因")
        return genes

    # ------------------------------------------------------------------
    # LLM 为用户选定的基因名解析物种（用于前端基因编辑器场景）
    # ------------------------------------------------------------------
    def extract_selected_genes_with_llm(
        self, answer_text: str, gene_names: list[str]
    ) -> list[dict]:
        """
        为用户在前端选定/添加的基因名，从回答上下文中解析对应物种。

        当用户通过基因编辑器修改了基因列表后，前端只发送基因名（无物种），
        此方法利用 LLM 从回答文本中推断每个基因的物种拉丁名。

        参数:
            answer_text: LLM 生成的回答全文（提供物种上下文）
            gene_names: 用户选定的基因名列表，如 ["GmFAD2", "AtMYB4"]

        返回:
            [{"gene": "GmFAD2", "species": "Glycine max"}, ...]

        异常:
            ValueError: 当未能为任何基因解析到物种信息时抛出
        """
        # gene_list_str: 逗号拼接的基因名列表，嵌入 prompt 中
        gene_list_str = ", ".join(gene_names)
        prompt = (
            f"以下是用户选定的基因列表：{gene_list_str}\n\n"
            "请根据下方文本的上下文，为每个基因确定其对应的物种（拉丁名）。\n"
            "如果文本中未提及某个基因的物种，请根据基因名前缀推断"
            "（如 Gm=Glycine max, At=Arabidopsis thaliana, Os=Oryza sativa, "
            "Sl=Solanum lycopersicum, Zm=Zea mays）。\n"
            '返回 JSON 数组格式: [{"gene": "GmFAD2", "species": "Glycine max"}]\n\n'
            f"文本：\n{answer_text}"
        )
        # messages: 发给 LLM 的消息列表（单轮对话）
        messages = [{"role": "user", "content": prompt}]

        resp = call_llm_sync(messages, temperature=0)

        # raw: LLM 返回的原始文本，兼容 markdown 代码块包裹格式
        raw = resp.content.strip()

        # ---- 兼容 markdown code block 格式 ----
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        genes = json.loads(raw.strip())
        if not isinstance(genes, list) or len(genes) == 0:
            raise ValueError("未能为选定的基因解析物种信息")
        return genes

    # ------------------------------------------------------------------
    # 全流程执行（接受基因列表，逐步执行 4 个步骤）
    # ------------------------------------------------------------------
    def run_all_from_genes(self, genes: list[dict]) -> Generator[dict, None, None]:
        """
        执行完整的 CRISPR 实验方案生成 pipeline。

        从基因列表开始，依次执行 4 个步骤，通过 yield 产出进度事件
        和最终结果，供 SSE 流式返回给前端。

        事件类型：
        - {"type": "progress", "step": N, "total": 4, "msg": "..."}  — 进度更新
        - {"type": "result", "sops": {accession: text, ...}}         — 最终结果
        - {"type": "error", "msg": "..."}                            — 错误信息

        参数:
            genes: 基因列表 [{"gene": "...", "species": "..."}, ...]

        Yields:
            进度事件字典
        """
        try:
            gene_names = ", ".join(g["gene"] for g in genes)

            # ---- Step 1: 基因名 → NCBI Accession ----
            yield {"type": "progress", "step": 1, "total": 4,
                   "msg": f"正在查询 NCBI 获取 accession（{gene_names}）..."}
            acc_file = step1_gene2acc.run_gene2accession(genes, self.work_dir)
            yield {"type": "progress", "step": 1, "total": 4,
                   "msg": "Accession 查询完成"}

            # ---- Step 2: Accession → FASTA 序列 ----
            yield {"type": "progress", "step": 2, "total": 4,
                   "msg": "正在从 NCBI 下载基因序列..."}
            fasta = step2_acc2seq.run_accession2sequence(acc_file, self.work_dir)
            yield {"type": "progress", "step": 2, "total": 4,
                   "msg": "序列下载完成"}

            # ---- Step 3: FASTA → CRISPR 靶点 ----
            yield {"type": "progress", "step": 3, "total": 4,
                   "msg": "正在设计 CRISPR 靶点（可能需要 10-30 秒）..."}
            targets = step3_crispr.run_crispr_target(fasta, self.work_dir)
            yield {"type": "progress", "step": 3, "total": 4,
                   "msg": "CRISPR 靶点设计完成"}

            # ---- Step 4: 靶点 → SOP 实验方案（按物种选择模板） ----
            yield {"type": "progress", "step": 4, "total": 4,
                   "msg": "正在生成实验方案 SOP..."}
            sops = step4_design.run_experiment_design(targets, self.work_dir, acc_file)
            yield {"type": "progress", "step": 4, "total": 4,
                   "msg": "实验方案生成完成"}

            # ---- 返回最终结果 ----
            yield {"type": "result", "sops": sops}

        except Exception as e:
            logger.exception("实验方案 pipeline 执行出错")
            yield {"type": "error", "msg": str(e)}

    # ------------------------------------------------------------------
    # 清理临时工作目录
    # ------------------------------------------------------------------
    def cleanup(self):
        """删除临时工作目录及其所有文件"""
        try:
            shutil.rmtree(self.work_dir, ignore_errors=True)
        except Exception:
            pass
