from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cachetools import TTLCache
from fastapi import Request

from nutrimaster.agent.agent import Agent
from nutrimaster.agent.skills import SkillLoader
from nutrimaster.agent.tools import ExperimentDesignTool, RagSearchTool, ToolRegistry
from nutrimaster.config.llm import call_llm
from nutrimaster.experiment import ExperimentDesignService
from nutrimaster.rag.jina import JinaRetriever
from nutrimaster.rag.personal_library import PersonalLibrary
from nutrimaster.rag.service import (
    GeneDbSource,
    PersonalLibrarySource,
    PubMedSource,
    RAGSearchService,
)
from nutrimaster.config.settings import Settings


@dataclass
class ReindexState:
    lock: threading.Lock = field(default_factory=threading.Lock)
    running: bool = False
    progress: str = ""
    error: str | None = None
    last_completed: str | None = None


@dataclass
class WebServices:
    settings: Settings
    retriever: JinaRetriever
    registry: Any
    skill_loader: Any
    agent: Agent
    experiment_service: ExperimentDesignService
    personal_libs: TTLCache = field(default_factory=lambda: TTLCache(maxsize=200, ttl=3600))
    personal_libs_lock: threading.Lock = field(default_factory=threading.Lock)
    reindex_state: ReindexState = field(default_factory=ReindexState)

    def get_personal_lib(self, user_id: str) -> PersonalLibrary:
        with self.personal_libs_lock:
            if user_id not in self.personal_libs:
                self.personal_libs[user_id] = PersonalLibrary(user_id)
            return self.personal_libs[user_id]

    def refresh_index(self, data_dir: Path | None = None, *, force: bool = False) -> None:
        kwargs: dict[str, Any] = {"incremental": True, "force": force}
        if data_dir is not None:
            kwargs["data_dir"] = data_dir
        self.retriever.build_index(**kwargs)
        if hasattr(self.retriever, "_bm25"):
            self.retriever._bm25 = None


def create_services(settings: Settings | None = None) -> WebServices:
    settings = settings or Settings.from_env()
    if settings.rag is None:
        raise RuntimeError("RAG settings failed to initialize")
    retriever = JinaRetriever(settings=settings)
    build_index = os.getenv("NUTRIMASTER_WEB_BUILD_INDEX", "").lower() in {"1", "true", "yes", "on"}

    holder: dict[str, WebServices] = {}

    def get_personal_lib(user_id: str) -> PersonalLibrary:
        return holder["services"].get_personal_lib(user_id)

    if build_index:
        retriever.build_index()

    registry = ToolRegistry()
    experiment_service = ExperimentDesignService()
    rag_service = RAGSearchService(
        pubmed_source=PubMedSource(),
        gene_db_source=GeneDbSource(retriever),
        personal_source=PersonalLibrarySource(
            get_personal_lib=get_personal_lib,
            get_query_embedding=retriever.get_query_embedding,
        ),
    )
    for tool in (RagSearchTool(rag_service), ExperimentDesignTool(experiment_service)):
        registry.register(tool)
    skill_loader = SkillLoader()

    services = WebServices(
        settings=settings,
        retriever=retriever,
        registry=registry,
        skill_loader=skill_loader,
        agent=Agent(registry=registry, skill_loader=skill_loader, call_llm=call_llm),
        experiment_service=experiment_service,
    )
    holder["services"] = services
    return services


def get_services(request: Request) -> WebServices:
    return request.app.state.services


def sse(payload: dict) -> str:
    import json

    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
