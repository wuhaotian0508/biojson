from __future__ import annotations

import json


def test_export_interactions_builds_sft_rows():
    from nutrimaster.agent.export_interactions import sft_rows

    record = {
        "record_type": "interaction",
        "interaction_id": "i1",
        "session_id": "s1",
        "turn_id": "t1",
        "created_at": "2026-01-01T00:00:00+00:00",
        "status": "completed",
        "request": {"query": "Q", "model_id": "m", "use_personal": False, "use_depth": True},
        "messages": [{"role": "user", "content": "Q"}],
        "final": {"answer_text": "A", "tools_used": ["rag_search"], "citations": [{"tool_index": 1}]},
    }
    rows = sft_rows([record], {"i1": {"rating": "up"}})

    assert rows == [
        {
            "schema_version": "dataset_export.v1",
            "task": "sft",
            "id": "i1",
            "source": "production",
            "messages": [{"role": "user", "content": "Q"}, {"role": "assistant", "content": "A"}],
            "metadata": {
                "session_id": "s1",
                "turn_id": "t1",
                "created_at": "2026-01-01T00:00:00+00:00",
                "model_id": "m",
                "use_personal": False,
                "use_depth": True,
                "tools_used": ["rag_search"],
                "citations": [{"tool_index": 1}],
                "feedback": "up",
            },
        }
    ]


def test_export_interactions_builds_preference_pairs():
    from nutrimaster.agent.export_interactions import preference_rows

    base = {
        "record_type": "interaction",
        "session_id": "s1",
        "turn_id": "t1",
        "status": "completed",
        "request": {"query": "same query"},
        "messages": [{"role": "user", "content": "same query"}],
    }
    chosen = {**base, "interaction_id": "up", "final": {"answer_text": "better"}}
    rejected = {**base, "interaction_id": "down", "final": {"answer_text": "worse"}}

    rows = preference_rows([chosen, rejected], {"up": {"rating": "up"}, "down": {"rating": "down"}})

    assert len(rows) == 1
    assert rows[0]["chosen"] == "better"
    assert rows[0]["rejected"] == "worse"


def test_export_interactions_writes_jsonl(tmp_path):
    from nutrimaster.agent.export_interactions import write_jsonl

    path = tmp_path / "out.jsonl"
    count = write_jsonl(path, [{"a": 1}, {"b": 2}])

    assert count == 2
    assert [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] == [{"a": 1}, {"b": 2}]
