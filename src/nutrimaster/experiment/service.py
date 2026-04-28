from __future__ import annotations

import asyncio
from typing import Any

from nutrimaster.experiment.crispr import run_crispr_workflow
from nutrimaster.experiment.gene_validation import verify_genes_with_ncbi
from nutrimaster.experiment.sop import format_sops


class ExperimentDesignService:
    """High-level CRISPR/SOP workflow boundary used by the agent and web API."""

    def __init__(self, pipeline_factory=None):
        self.pipeline_factory = pipeline_factory

    async def preview(
        self,
        *,
        goal: str,
        genes: list[dict[str, Any]] | None = None,
        selected_gene_names: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        pipeline = self._create_pipeline()
        try:
            if genes:
                extracted = genes
            elif selected_gene_names:
                extracted = await asyncio.to_thread(
                    pipeline.extract_selected_genes_with_llm,
                    goal,
                    selected_gene_names,
                )
            else:
                extracted = await asyncio.to_thread(pipeline.extract_genes_with_llm, goal)
            return await asyncio.to_thread(verify_genes_with_ncbi, extracted)
        finally:
            pipeline.cleanup()

    async def run(self, *, genes: list[dict[str, Any]]) -> dict[str, str]:
        pipeline = self._create_pipeline()
        try:
            return await asyncio.to_thread(run_crispr_workflow, pipeline, genes)
        finally:
            pipeline.cleanup()

    async def tool_call(
        self,
        *,
        goal: str,
        genes: list[dict[str, Any]] | None = None,
        output: str = "advice",
        confirmed: bool = False,
    ) -> str:
        preview_genes = await self.preview(goal=goal, genes=genes)
        if output != "full_sop" or not confirmed:
            lines = ["实验设计预览：", ""]
            for gene in preview_genes:
                lines.append(f"- {gene.get('gene', '')} ({gene.get('species', '')})")
            lines.append("")
            lines.append("如需完整 CRISPR/SOP，请明确要求生成完整实验方案。")
            return "\n".join(lines)
        return format_sops(await self.run(genes=preview_genes))

    def _create_pipeline(self):
        if self.pipeline_factory is not None:
            return self.pipeline_factory()
        from nutrimaster.crispr.pipeline import ExperimentPipeline

        return ExperimentPipeline()
