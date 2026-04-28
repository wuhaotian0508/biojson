from __future__ import annotations


def test_web_services_register_only_high_level_agent_tools(monkeypatch):
    from nutrimaster.web.deps import create_services
    import nutrimaster.web.deps as deps

    class FakeRetriever:
        chunks = []

        def __init__(self, *_, **__):
            pass

        def hybrid_search(self, *_, **__):
            return []

        def get_query_embedding(self, query):
            return []

    monkeypatch.setattr(deps, "JinaRetriever", FakeRetriever)
    services = create_services()

    assert services.registry.tool_names == {"rag_search", "experiment_design"}
    assert "pubmed_search" not in services.registry.tool_names
    assert "gene_db_search" not in services.registry.tool_names
    assert "execute_shell" not in services.registry.tool_names


def test_removed_agent_assembly_modules_are_gone():
    import importlib.util

    assert importlib.util.find_spec("nutrimaster.agent.stack") is None
    assert importlib.util.find_spec("nutrimaster.agent.runtime") is None
    assert importlib.util.find_spec("nutrimaster.agent.tool_policy") is None
