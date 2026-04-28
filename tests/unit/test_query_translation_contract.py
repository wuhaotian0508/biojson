from __future__ import annotations


def test_query_translator_enhances_terms_with_injected_llm():
    import asyncio

    from nutrimaster.rag.query_translation import QueryTranslator

    async def call_llm(prompt):
        assert "番茄果实" in prompt
        return '{"番茄": "tomato", "果实": "fruit", "类胡萝卜素": "carotenoid"}'

    translator = QueryTranslator(call_llm=call_llm)

    assert asyncio.run(translator.translate_query_terms("番茄果实中类胡萝卜素")) == (
        "番茄 tomato 果实 fruit 中类胡萝卜素 carotenoid"
    )


def test_query_translator_returns_original_query_without_llm():
    import asyncio

    from nutrimaster.rag.query_translation import QueryTranslator

    assert asyncio.run(QueryTranslator(call_llm=None).translate_query_terms("lycopene")) == "lycopene"
