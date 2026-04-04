"""RAG Pipeline — 编排 搜索 → 检索 → rerank → 生成 的完整流程"""
import logging
from dataclasses import dataclass, field
from typing import Generator, Dict, List

from config import (
    DEEP_TOP_K_RETRIEVAL, DEEP_TOP_K_RERANK, TOP_K_RERANK,
)

logger = logging.getLogger(__name__)


@dataclass
class QueryOptions:
    """查询选项"""
    use_personal: bool = False
    use_depth: bool = False
    history: list = field(default_factory=list)
    user: object = None          # request.user，用于获取个人库


class RAGPipeline:
    """RAG 查询编排：搜索 → 检索 → rerank → 生成"""

    def __init__(self, retriever, online_searcher, reranker, generator,
                 skill_loader, get_personal_lib=None):
        self.retriever = retriever
        self.online_searcher = online_searcher
        self.reranker = reranker
        self.generator = generator
        self.skill_loader = skill_loader
        self._get_personal_lib = get_personal_lib

    # ------------------------------------------------------------------
    # 主流程
    # ------------------------------------------------------------------
    def run(self, query: str, opts: QueryOptions) -> Generator[dict, None, None]:
        """执行完整 RAG 流程，yield 事件 dict。

        事件类型：
          searching, sources, text, genes_available,
          experiment_start, progress, result, done, error
        """
        try:
            # ---- 快速路径：用户明确要求 SOP ----
            if self.skill_loader.should_trigger(query=query, trigger_source="query"):
                early = yield from self._try_sop_fast_path(query, opts.history)
                if early:
                    return

            all_candidates: List[Dict] = []

            # 1) 联网搜索 — 始终执行
            yield {"type": "searching", "data": "正在搜索 PubMed 文献..."}
            online_results = self.online_searcher.search_all(query)
            all_candidates.extend(online_results)

            # 2) 基因库检索 — 仅深度模式
            if opts.use_depth:
                yield {"type": "searching", "data": "正在检索基因数据库（深度模式）..."}
                gene_candidates = self.retriever.search(query, top_k=DEEP_TOP_K_RETRIEVAL)
                all_candidates.extend(self._gene_chunks_to_dicts(gene_candidates))

            # 3) 个人库检索
            if opts.use_personal and opts.user and self._get_personal_lib:
                yield {"type": "searching", "data": "正在检索个人知识库..."}
                try:
                    lib = self._get_personal_lib(opts.user)
                    q_emb = self.retriever.get_query_embedding(query)
                    personal_results = lib.search(q_emb, top_k=10)
                    all_candidates.extend(personal_results)
                except Exception as e:
                    logger.warning("Personal lib search failed: %s", e)

            # 4) 统一 rerank
            if all_candidates:
                yield {"type": "searching", "data": "正在对结果进行排序..."}
                top_n = DEEP_TOP_K_RERANK if opts.use_depth else TOP_K_RERANK
                ranked = self.reranker.rerank(query, all_candidates, top_n)
            else:
                ranked = []

            # 5) 发送来源
            yield {"type": "sources", "data": self._build_sources(ranked)}

            # 6) LLM 生成
            answer_text = ""
            for event in self.generator.generate_stream_with_tools(
                query, ranked, use_depth=opts.use_depth, history=opts.history,
            ):
                if event["type"] == "text":
                    answer_text += event["data"]
                    yield {"type": "text", "data": event["data"]}

            # 7) SOP 自动触发 / 基因名检测
            yield from self._post_generate(query, answer_text)

            yield {"type": "done"}

        except Exception as e:
            logger.exception("Pipeline error")
            yield {"type": "error", "data": str(e)}

    # ------------------------------------------------------------------
    # 实验 pipeline
    # ------------------------------------------------------------------
    def run_experiment(self, tool_call: dict) -> Generator[dict, None, None]:
        """执行实验 SOP pipeline，yield 事件。"""
        from skills.crispr_experiment.pipeline import ExperimentPipeline

        skill_name = tool_call.get("skill", "crispr-experiment")
        self.skill_loader.get_skill(skill_name)
        args = tool_call.get("args", {})

        pipeline = ExperimentPipeline()
        try:
            genes = self._resolve_experiment_genes(pipeline, args)
            yield {
                "type": "experiment_start",
                "genes": [g["gene"] for g in genes],
            }
            for event in pipeline.run_all_from_genes(genes):
                yield event
        finally:
            pipeline.cleanup()

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------
    def _try_sop_fast_path(self, query: str, history: list) -> Generator[dict, None, bool]:
        """SOP 快速路径：跳过检索直接执行 pipeline。返回 True 表示已处理。"""
        from skills.crispr_experiment.pipeline import ExperimentPipeline

        prev_answer = ""
        for msg in reversed(history):
            if msg.get("role") == "assistant" and msg.get("content"):
                prev_answer = msg["content"]
                break

        tool_call = self.skill_loader.build_tool_call(
            query=query, answer_text=prev_answer, trigger_source="query",
        )
        if not tool_call:
            return False

        pipeline = ExperimentPipeline()
        try:
            yield {"type": "searching", "data": "正在提取基因..."}
            genes = self._resolve_experiment_genes(pipeline, tool_call.get("args", {}))
            gene_names = [g["gene"] for g in genes if g.get("gene")]
            if gene_names:
                yield {"type": "genes_available", "genes": gene_names}
                yield {"type": "done"}
                return True
        except Exception:
            logger.info("SOP 快速路径基因提取失败，回退到常规流程")
        finally:
            pipeline.cleanup()

        return False

    def _post_generate(self, query: str, answer_text: str) -> Generator[dict, None, None]:
        """生成完成后：检测 SOP 自动触发或提取基因名。"""
        auto_trigger = self.skill_loader.should_trigger(
            query=query, answer_text=answer_text, trigger_source="query",
        )

        if auto_trigger and answer_text:
            tool_call = self.skill_loader.build_tool_call(
                query=query, answer_text=answer_text, trigger_source="query",
            )
            if tool_call:
                yield from self.run_experiment(tool_call)

        elif answer_text:
            detected_genes = self.skill_loader.extract_gene_names(answer_text)
            if detected_genes:
                yield {"type": "genes_available", "genes": detected_genes}

    @staticmethod
    def _resolve_experiment_genes(pipeline, args: dict) -> list[dict]:
        """解析待编辑基因列表（3 种来源）。"""
        # 路径 1: 完整基因列表
        genes = args.get("genes")
        if genes:
            return genes

        # 路径 2: 用户选定的基因名（需 LLM 解析物种）
        genes_selected = args.get("genes_selected")
        if genes_selected:
            source_text = (args.get("answer_text") or args.get("query") or "").strip()
            return pipeline.extract_selected_genes_with_llm(source_text, genes_selected)

        # 路径 3: 自动提取
        query_text = (args.get("query") or "").strip()
        answer_text = (args.get("answer_text") or "").strip()
        source_text = f"{query_text}\n{answer_text}".strip()
        if not source_text:
            raise ValueError("缺少可用于提取基因的 query 或 answer_text")
        return pipeline.extract_genes_with_llm(source_text)

    @staticmethod
    def _gene_chunks_to_dicts(chunks) -> List[Dict]:
        """将 (GeneChunk, score) 列表转为统一 dict 格式。"""
        results = []
        for chunk, score in chunks:
            results.append({
                "source_type": "gene_db",
                "title": chunk.paper_title,
                "content": chunk.content,
                "url": chunk.doi or "",
                "score": float(score),
                "metadata": {
                    "gene_name": chunk.gene_name,
                    "journal": chunk.journal,
                    "gene_type": chunk.gene_type,
                    "doi": chunk.doi,
                },
            })
        return results

    @staticmethod
    def _build_sources(ranked: List[Dict]) -> list:
        """从 ranked 结果构建前端 sources 列表。"""
        sources = []
        for item in ranked:
            meta = item.get("metadata", {})
            sources.append({
                "source_type": item["source_type"],
                "title": item.get("title", ""),
                "score": item.get("score", 0.0),
                "url": item.get("url", ""),
                "paper_title": item.get("title", ""),
                "gene_name": meta.get("gene_name", ""),
                "journal": meta.get("journal", ""),
                "doi": meta.get("doi", ""),
                "pmid": meta.get("pmid", ""),
                "filename": meta.get("filename", ""),
                "page": meta.get("page", ""),
            })
        return sources
