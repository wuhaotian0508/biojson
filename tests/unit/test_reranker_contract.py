from __future__ import annotations


def test_jina_reranker_uses_injected_post_and_updates_scores():
    from nutrimaster.rag.jina import JinaReranker

    calls = []

    def post_json(url, payload, headers, timeout):
        calls.append((url, payload, headers, timeout))
        return {
            "results": [
                {"index": 1, "relevance_score": 0.95},
                {"index": 0, "relevance_score": 0.5},
            ]
        }

    reranker = JinaReranker(
        api_key="jina-key",
        rerank_url="https://jina.test/rerank",
        model="rerank-model",
        post_json=post_json,
    )
    ranked = reranker.rerank(
        "lycopene",
        [
            {"content": "low", "score": 0.0},
            {"content": "high", "score": 0.0},
        ],
        top_n=2,
    )

    assert [item["content"] for item in ranked] == ["high", "low"]
    assert [item["score"] for item in ranked] == [0.95, 0.5]
    assert calls[0][1]["model"] == "rerank-model"
    assert calls[0][2]["Authorization"] == "Bearer jina-key"
