from __future__ import annotations

from typing import Any

# 基础工具类定义: src/nutrimaster/agent/tools/base.py (第11-26行)
from nutrimaster.agent.tools.base import BaseTool
# 实验设计服务实现: src/nutrimaster/experiment/service.py
# ExperimentDesignService.tool_call() 方法 (第47-63行):
#   async def tool_call(self, *, goal: str, genes: list[dict[str, Any]] | None = None,
#                       output: str = "advice", confirmed: bool = False) -> str:
#       preview_genes = await self.preview(goal=goal, genes=genes)
#       if output != "full_sop" or not confirmed:
#           lines = ["实验设计预览：", ""]
#           for gene in preview_genes:
#               lines.append(f"- {gene.get('gene', '')} ({gene.get('species', '')})")
#           lines.append("")
#           lines.append("如需完整 CRISPR/SOP，请明确要求生成完整实验方案。")
#           return "\n".join(lines)
#       return format_sops(await self.run(genes=preview_genes))
from nutrimaster.experiment import ExperimentDesignService


class ExperimentDesignTool(BaseTool):
    name = "experiment_design"
    description = "一键实验设计工具：解析基因/物种，进行 CRISPR 靶点设计并生成实验建议或完整 SOP"

    def __init__(self, service: ExperimentDesignService):
        self.service = service

    @property
    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "goal": {
                            "type": "string",
                            "description": "用户的实验目标或原始需求。",
                        },
                        "genes": {
                            "type": "array",
                            "description": "可选。已知基因列表，每项包含 gene 和 species。",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "gene": {"type": "string"},
                                    "species": {"type": "string"},
                                },
                                "required": ["gene"],
                            },
                        },
                        "output": {
                            "type": "string",
                            "enum": ["advice", "full_sop"],
                            "description": "advice 返回实验建议；full_sop 生成完整 SOP。",
                        },
                        "confirmed": {
                            "type": "boolean",
                            "description": "是否确认运行完整 pipeline。未确认时只返回预览。",
                        },
                    },
                    "required": ["goal"],
                },
            },
        }

    async def execute(
        self,
        goal: str,
        genes: list[dict[str, Any]] | None = None,
        output: str = "advice",
        confirmed: bool = False,
        **_,
    ) -> str:
        return await self.service.tool_call(
            goal=goal,
            genes=genes,
            output=output,
            confirmed=confirmed,
        )
