from __future__ import annotations


def test_personal_lib_search_tool_uses_callbacks_and_formats_results():
    import asyncio
    import inspect

    from nutrimaster.agent.tools.retrieval import PersonalLibSearchTool
    import nutrimaster.agent.tools.retrieval.personal_lib as personal_module

    assert "rag.tools" not in inspect.getsource(personal_module)

    class FakeLibrary:
        def search(self, query_embedding, top_k):
            assert query_embedding == [1.0, 2.0]
            assert top_k == 3
            return [
                {
                    "source_type": "personal",
                    "title": "paper.pdf (p.1)",
                    "content": "lycopene content",
                    "url": "",
                    "score": 0.8,
                    "metadata": {"filename": "paper.pdf", "page": 1},
                }
            ]

    tool = PersonalLibSearchTool(
        get_personal_lib=lambda user_id: FakeLibrary() if user_id == "user-1" else None,
        get_query_embedding=lambda query: [1.0, 2.0],
    )

    raw = asyncio.run(tool.search_raw("lycopene", user_id="user-1", top_k=3))
    assert raw[0]["metadata"]["filename"] == "paper.pdf"
    rendered = asyncio.run(tool.execute("lycopene", user_id="user-1", top_k=3))
    assert "个人知识库检索结果" in rendered
    assert "lycopene content" in rendered


def test_personal_lib_search_tool_degrades_without_user_context():
    import asyncio

    from nutrimaster.agent.tools.retrieval import PersonalLibSearchTool

    tool = PersonalLibSearchTool()

    assert asyncio.run(tool.search_raw("lycopene")) == []
    assert asyncio.run(tool.execute("lycopene")) == "个人知识库未配置或用户未登录。"
