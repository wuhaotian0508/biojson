from __future__ import annotations

import asyncio
import logging

from nutrimaster.agent.tools.base import BaseTool

logger = logging.getLogger(__name__)


class CrisprTool(BaseTool):
    name = "design_crispr_experiment"
    description = "为指定基因设计完整的 CRISPR/SpCas9 基因编辑实验方案(SOP)"

    def __init__(self, *, pipeline_factory=None):
        self._pipeline_factory = pipeline_factory

    @property
    def schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": (
                    "为指定基因设计完整的 CRISPR/SpCas9 基因编辑实验方案(SOP)。"
                    "自动查询 NCBI、下载序列、设计靶点、生成实验方案。"
                    "第一次调用时 confirmed 传 false，返回预览信息让用户确认；"
                    "用户确认后再以 confirmed=true 调用执行 pipeline。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "genes": {
                            "type": "array",
                            "description": "基因列表，每个元素含 gene(基因名) 和 species(物种拉丁名)",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "gene": {
                                        "type": "string",
                                        "description": "基因名，如 GmFAD2",
                                    },
                                    "species": {
                                        "type": "string",
                                        "description": "物种拉丁名，如 Glycine max",
                                    },
                                },
                                "required": ["gene", "species"],
                            },
                        },
                        "confirmed": {
                            "type": "boolean",
                            "description": "是否已确认执行。false=预览，true=执行pipeline",
                        },
                    },
                    "required": ["genes"],
                },
            },
        }

    async def execute(self, genes, confirmed=False, **_):
        if not confirmed:
            lines = ["即将为以下基因设计 CRISPR/SpCas9 实验方案：", ""]
            for gene in genes:
                lines.append(f"  - {gene['gene']} ({gene['species']})")
            lines.append("")
            lines.append("流程包括：查询 NCBI accession → 下载序列 → 设计 CRISPR 靶点 → 生成 SOP")
            lines.append("整个过程可能需要 1-3 分钟，请确认是否继续。")
            return "\n".join(lines)

        try:
            results, errors = await asyncio.get_event_loop().run_in_executor(None, self._run_pipeline, genes)
        except Exception as exc:
            return f"Pipeline 执行失败：{exc}"

        if errors:
            return "Pipeline 执行中出现错误：\n" + "\n".join(errors)
        if not results:
            return "Pipeline 执行完成，但未生成任何 SOP。请检查基因名和物种是否正确。"

        output = [f"成功为 {len(results)} 个基因生成了实验方案：\n"]
        for accession, sop_text in results.items():
            output.append(f"--- {accession} ---")
            output.append(sop_text)
            output.append("")
        return "\n".join(output)

    def _run_pipeline(self, genes):
        pipeline = self._create_pipeline()
        try:
            results = {}
            errors = []
            for event in pipeline.run_all_from_genes(genes):
                if event["type"] == "progress":
                    logger.info("[%d/%d] %s", event["step"], event["total"], event["msg"])
                elif event["type"] == "result":
                    results = event["sops"]
                elif event["type"] == "error":
                    errors.append(event["msg"])
            return results, errors
        finally:
            pipeline.cleanup()

    def _create_pipeline(self):
        if self._pipeline_factory is not None:
            return self._pipeline_factory()
        from nutrimaster.crispr.pipeline import ExperimentPipeline

        return ExperimentPipeline()
