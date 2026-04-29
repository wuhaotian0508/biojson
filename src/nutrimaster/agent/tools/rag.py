from __future__ import annotations

from nutrimaster.agent.tools.base import BaseTool
from nutrimaster.rag.evidence import EvidencePacket
from nutrimaster.rag.service import RAGSearchContext, RAGSearchService


class RagSearchTool(BaseTool):
    name = "rag_search"
    description = "复合 RAG 检索：检索 PubMed 摘要和本地基因库，必要时加入个人库，并返回带编号证据"

    def __init__(self, service: RAGSearchService):
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
                        "query": {
                            "type": "string",
                            "description": "本地基因库的语义检索词。保留关键基因、通路、物种、代谢物，可用中英混合。",
                        },
                        "pubmed_query": {
                            "type": "string",
                            "description": "可选。Agent 自行生成的英文 PubMed 检索式/关键词，如 HY5 AND alkaloid AND photoreceptor。",
                        },
                        "gene_db_query": {
                            "type": "string",
                            "description": "可选。本地基因库专用检索词；不填时使用 query。",
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["normal", "deep"],
                            "description": "normal 或 deep。两者都会检索 PubMed 和基因库，deep 会增加召回预算。",
                        },
                        "include_personal": {
                            "type": "boolean",
                            "description": "是否加入个人知识库。用户未开启个人库时保持 false。",
                        },
                        "focus": {
                            "type": "string",
                            "description": "检索重点，如 gene_function、pathway、literature、experiment、general。",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "融合后返回证据数量，默认 10。",
                        },
                    },
                    "required": ["query"],
                },
            },
        }

    async def execute(
        self,
        query: str,
        pubmed_query: str = "",
        gene_db_query: str = "",
        mode: str = "normal",
        include_personal: bool = False,
        focus: str = "general",
        top_k: int = 10,
        user_id: str | None = None,
        **_,
    ) -> EvidencePacket:
        return await self.service.search(
            query,
            RAGSearchContext(
                user_id=user_id,
                include_personal=include_personal,
                mode=mode,
                focus=focus,
                top_k=top_k,
                pubmed_query=pubmed_query,
                gene_db_query=gene_db_query,
            ),
        )
