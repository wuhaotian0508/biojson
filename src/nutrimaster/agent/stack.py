from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from nutrimaster.agent.agent import Agent
from nutrimaster.agent.runtime import AgentRuntime
from nutrimaster.agent.skills import SkillLoader
from nutrimaster.agent.tool_policy import ToolPolicy
from nutrimaster.agent.tools import CrisprTool, ReadTool, ShellTool, WriteTool
from nutrimaster.config.llm import call_llm, call_llm_stream
from nutrimaster.config.settings import Settings
from nutrimaster.rag.query_translation import configure_llm as configure_query_translator
from nutrimaster.rag.reranking import JinaReranker
from nutrimaster.agent.tools import ToolRegistry
from nutrimaster.agent.tools.retrieval import (
    GeneDBSearchTool,
    PersonalLibSearchTool,
    PubmedQueryOptimizer,
    PubmedSearchTool,
    RAGSearchTool,
)


@dataclass(frozen=True)
class AgentStack:
    retriever: Any
    registry: Any
    skill_loader: Any
    agent_runtime: AgentRuntime
    tools: dict[str, Any]

    @property
    def tool_names(self) -> set[str]:
        return set(self.tools)


def build_agent_stack(
    *,
    retriever: Any | None = None,
    registry_factory: Callable[[], Any] | None = None,
    skill_loader_factory: Callable[[], Any] | None = None,
    agent_factory: Callable[..., Any] | None = None,
    call_llm: Callable | None = None,
    call_llm_stream: Callable | None = None,
    pubmed_tool_factory: Callable[[], Any] | None = None,
    gene_db_tool_factory: Callable[[Any], Any] | None = None,
    personal_lib_tool_factory: Callable[[], Any] | None = None,
    rag_search_tool_factory: Callable[[dict[str, Any], Any], Any] | None = None,
    crispr_tool_factory: Callable[[], Any] | None = None,
    read_tool_factory: Callable[[], Any] | None = None,
    write_tool_factory: Callable[[], Any] | None = None,
    shell_tool_factory: Callable[[], Any] | None = None,
    reranker_factory: Callable[[], Any] | None = None,
    configure_query_translator: Callable[..., Any] | None = None,
    configure_query_optimizer: Callable[..., Any] | None = None,
    llm_api_key: str | None = None,
    llm_base_url: str | None = None,
    utility_model: str = "gpt-4o-mini",
    tool_policy: ToolPolicy | None = None,
    build_index: bool = True,
) -> AgentStack:
    """Build the NutriMaster agent stack behind a single composition boundary."""

    needs_defaults = any(
        item is None
        for item in (
            retriever,
            registry_factory,
            skill_loader_factory,
            agent_factory,
            call_llm,
            call_llm_stream,
            pubmed_tool_factory,
            gene_db_tool_factory,
            personal_lib_tool_factory,
            rag_search_tool_factory,
            crispr_tool_factory,
            read_tool_factory,
            write_tool_factory,
            shell_tool_factory,
            reranker_factory,
        )
    )
    if needs_defaults:
        defaults = _defaults()
        retriever = retriever or defaults["retriever_factory"]()
        registry_factory = registry_factory or defaults["registry_factory"]
        skill_loader_factory = skill_loader_factory or defaults["skill_loader_factory"]
        agent_factory = agent_factory or defaults["agent_factory"]
        call_llm = call_llm or defaults["call_llm"]
        call_llm_stream = call_llm_stream or defaults["call_llm_stream"]
        pubmed_tool_factory = pubmed_tool_factory or defaults["pubmed_tool_factory"]
        gene_db_tool_factory = gene_db_tool_factory or defaults["gene_db_tool_factory"]
        personal_lib_tool_factory = personal_lib_tool_factory or defaults["personal_lib_tool_factory"]
        rag_search_tool_factory = rag_search_tool_factory or defaults["rag_search_tool_factory"]
        crispr_tool_factory = crispr_tool_factory or defaults["crispr_tool_factory"]
        read_tool_factory = read_tool_factory or defaults["read_tool_factory"]
        write_tool_factory = write_tool_factory or defaults["write_tool_factory"]
        shell_tool_factory = shell_tool_factory or defaults["shell_tool_factory"]
        reranker_factory = reranker_factory or defaults["reranker_factory"]
        configure_query_translator = configure_query_translator or defaults["configure_query_translator"]
        configure_query_optimizer = configure_query_optimizer or defaults["configure_query_optimizer"]
        llm_api_key = llm_api_key if llm_api_key is not None else defaults["llm_api_key"]
        llm_base_url = llm_base_url if llm_base_url is not None else defaults["llm_base_url"]

    if configure_query_translator is not None:
        configure_query_translator(
            api_key=llm_api_key,
            base_url=llm_base_url,
            model=utility_model,
        )
    if configure_query_optimizer is not None:
        configure_query_optimizer(
            api_key=llm_api_key,
            base_url=llm_base_url,
            model=utility_model,
        )

    if build_index and hasattr(retriever, "build_index"):
        retriever.build_index()

    registry = registry_factory()
    reranker = reranker_factory()
    pubmed_tool = pubmed_tool_factory()
    gene_db_tool = gene_db_tool_factory(retriever)
    personal_lib_tool = personal_lib_tool_factory()
    rag_search_tool = rag_search_tool_factory(
        {
            "pubmed": pubmed_tool,
            "gene_db": gene_db_tool,
            "personal_lib": personal_lib_tool,
        },
        reranker,
    )
    crispr_tool = crispr_tool_factory()
    read_tool = read_tool_factory()
    write_tool = write_tool_factory()
    shell_tool = shell_tool_factory()

    candidates = {
        pubmed_tool.name: pubmed_tool,
        gene_db_tool.name: gene_db_tool,
        personal_lib_tool.name: personal_lib_tool,
        rag_search_tool.name: rag_search_tool,
        crispr_tool.name: crispr_tool,
        read_tool.name: read_tool,
        write_tool.name: write_tool,
        shell_tool.name: shell_tool,
    }
    enabled = (tool_policy or ToolPolicy.default_user()).enabled_tools()
    tools = {name: tool for name, tool in candidates.items() if name in enabled}
    for tool in tools.values():
        registry.register(tool)

    skill_loader = skill_loader_factory()
    agent = agent_factory(
        registry=registry,
        skill_loader=skill_loader,
        call_llm=call_llm,
        call_llm_stream=call_llm_stream,
    )
    return AgentStack(
        retriever=retriever,
        registry=registry,
        skill_loader=skill_loader,
        agent_runtime=AgentRuntime(agent),
        tools=tools,
    )


def _defaults() -> dict[str, Any]:
    from nutrimaster.rag.jina_retriever import JinaRetriever

    settings = Settings.from_env()
    if settings.rag is None:
        raise RuntimeError("RAG settings failed to initialize")
    return {
        "retriever_factory": JinaRetriever,
        "registry_factory": ToolRegistry,
        "skill_loader_factory": SkillLoader,
        "agent_factory": Agent,
        "call_llm": call_llm,
        "call_llm_stream": call_llm_stream,
        "pubmed_tool_factory": lambda: PubmedSearchTool(
            query_optimizer=PubmedQueryOptimizer(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model="gpt-4o-mini",
            )
        ),
        "gene_db_tool_factory": GeneDBSearchTool,
        "personal_lib_tool_factory": PersonalLibSearchTool,
        "rag_search_tool_factory": RAGSearchTool,
        "crispr_tool_factory": CrisprTool,
        "read_tool_factory": ReadTool,
        "write_tool_factory": WriteTool,
        "shell_tool_factory": ShellTool,
        "reranker_factory": lambda: JinaReranker(
            api_key=settings.jina_api_key,
            rerank_url=settings.rag.jina_rerank_url,
            model=settings.rag.rerank_model,
        ),
        "configure_query_translator": configure_query_translator,
        "configure_query_optimizer": lambda **_: None,
        "llm_api_key": settings.openai_api_key,
        "llm_base_url": settings.openai_base_url,
    }


__all__ = ["AgentStack", "build_agent_stack"]
