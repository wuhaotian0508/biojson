from __future__ import annotations

import inspect


class FakeTool:
    def __init__(self, name: str):
        self.name = name
        self.description = name


class FakeRegistry:
    def __init__(self):
        self.registered = []

    def register(self, tool):
        self.registered.append(tool)

    @property
    def tool_names(self):
        return {tool.name for tool in self.registered}


class FakeAgent:
    def __init__(self, *, registry, skill_loader, call_llm, call_llm_stream):
        self.registry = registry
        self.skill_loader = skill_loader
        self.call_llm = call_llm
        self.call_llm_stream = call_llm_stream

    async def run(self, **kwargs):
        yield {"type": "done", "kwargs": kwargs}


def test_agent_stack_defaults_do_not_depend_on_legacy_core_config_or_sys_path():
    import nutrimaster.agent.stack as stack_module

    source = inspect.getsource(stack_module)

    assert "from core import config" not in source
    assert "sys.path.insert" not in source
    assert "Settings.from_env" in source


def test_agent_stack_factory_registers_default_user_tools():
    from nutrimaster.agent.stack import build_agent_stack
    from nutrimaster.agent.tool_policy import ToolPolicy

    stack = build_agent_stack(
        retriever=object(),
        registry_factory=FakeRegistry,
        skill_loader_factory=lambda: object(),
        agent_factory=FakeAgent,
        call_llm=lambda *_, **__: None,
        call_llm_stream=lambda *_, **__: None,
        pubmed_tool_factory=lambda: FakeTool("pubmed_search"),
        gene_db_tool_factory=lambda retriever: FakeTool("gene_db_search"),
        personal_lib_tool_factory=lambda: FakeTool("personal_lib_search"),
        rag_search_tool_factory=lambda sources, reranker: FakeTool("rag_search"),
        crispr_tool_factory=lambda: FakeTool("design_crispr_experiment"),
        read_tool_factory=lambda: FakeTool("read_tool"),
        write_tool_factory=lambda: FakeTool("write_tool"),
        shell_tool_factory=lambda: FakeTool("execute_shell"),
        reranker_factory=lambda: object(),
        tool_policy=ToolPolicy.default_user(),
        build_index=False,
    )

    assert stack.tool_names == {
        "pubmed_search",
        "gene_db_search",
        "personal_lib_search",
        "rag_search",
        "design_crispr_experiment",
        "read_tool",
        "write_tool",
        "execute_shell",
    }


def test_agent_stack_factory_respects_disabled_policy():
    from nutrimaster.agent.stack import build_agent_stack
    from nutrimaster.agent.tool_policy import ToolPolicy

    stack = build_agent_stack(
        retriever=object(),
        registry_factory=FakeRegistry,
        skill_loader_factory=lambda: object(),
        agent_factory=FakeAgent,
        call_llm=lambda *_, **__: None,
        call_llm_stream=lambda *_, **__: None,
        pubmed_tool_factory=lambda: FakeTool("pubmed_search"),
        gene_db_tool_factory=lambda retriever: FakeTool("gene_db_search"),
        personal_lib_tool_factory=lambda: FakeTool("personal_lib_search"),
        rag_search_tool_factory=lambda sources, reranker: FakeTool("rag_search"),
        crispr_tool_factory=lambda: FakeTool("design_crispr_experiment"),
        read_tool_factory=lambda: FakeTool("read_tool"),
        write_tool_factory=lambda: FakeTool("write_tool"),
        shell_tool_factory=lambda: FakeTool("execute_shell"),
        reranker_factory=lambda: object(),
        tool_policy=ToolPolicy.default_user().with_disabled({"execute_shell"}),
        build_index=False,
    )

    assert "execute_shell" not in stack.tool_names
    assert "read_tool" in stack.tool_names


def test_agent_stack_factory_configures_query_helpers():
    from nutrimaster.agent.stack import build_agent_stack

    calls = []

    build_agent_stack(
        retriever=object(),
        registry_factory=FakeRegistry,
        skill_loader_factory=lambda: object(),
        agent_factory=FakeAgent,
        call_llm=lambda *_, **__: None,
        call_llm_stream=lambda *_, **__: None,
        pubmed_tool_factory=lambda: FakeTool("pubmed_search"),
        gene_db_tool_factory=lambda retriever: FakeTool("gene_db_search"),
        personal_lib_tool_factory=lambda: FakeTool("personal_lib_search"),
        rag_search_tool_factory=lambda sources, reranker: FakeTool("rag_search"),
        crispr_tool_factory=lambda: FakeTool("design_crispr_experiment"),
        read_tool_factory=lambda: FakeTool("read_tool"),
        write_tool_factory=lambda: FakeTool("write_tool"),
        shell_tool_factory=lambda: FakeTool("execute_shell"),
        reranker_factory=lambda: object(),
        configure_query_translator=lambda **kwargs: calls.append(("translator", kwargs)),
        configure_query_optimizer=lambda **kwargs: calls.append(("optimizer", kwargs)),
        llm_api_key="key",
        llm_base_url="https://example.test/v1",
        utility_model="fast-model",
        build_index=False,
    )

    assert calls == [
        (
            "translator",
            {
                "api_key": "key",
                "base_url": "https://example.test/v1",
                "model": "fast-model",
            },
        ),
        (
            "optimizer",
            {
                "api_key": "key",
                "base_url": "https://example.test/v1",
                "model": "fast-model",
            },
        ),
    ]
