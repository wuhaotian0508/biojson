from __future__ import annotations

import json


def test_interaction_recorder_records_by_default_without_consent(monkeypatch, tmp_path):
    from nutrimaster.agent.interaction_recording import InteractionRecorder
    from nutrimaster.config.settings import Settings

    monkeypatch.setenv("NUTRIMASTER_INTERACTION_CAPTURE_ENABLED", "true")
    monkeypatch.delenv("NUTRIMASTER_INTERACTION_CAPTURE_REQUIRE_CONSENT", raising=False)
    monkeypatch.setenv("NUTRIMASTER_INTERACTION_CAPTURE_DIR", str(tmp_path))

    recorder = InteractionRecorder.from_settings(Settings.from_env(env={}, project_root=tmp_path))
    session = recorder.start(
        user_id="user-1",
        session_id="session-1",
        client_turn_id="turn-1",
        query="hello",
        model_id="model",
        history=[],
        initial_messages=[{"role": "user", "content": "hello"}],
        use_personal=False,
        use_depth=False,
        capture_consent=False,
    )
    session.capture_event({"type": "text", "data": "answer"})
    session.finish()

    rows = [json.loads(line) for line in (tmp_path / "interactions.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[0]["consent"] == {"granted": True, "required": False, "privacy_level": "standard"}
    assert rows[0]["final"]["answer_text"] == "answer"


def test_interaction_recorder_requires_consent(monkeypatch, tmp_path):
    from nutrimaster.agent.interaction_recording import InteractionRecorder
    from nutrimaster.config.settings import Settings

    monkeypatch.setenv("NUTRIMASTER_INTERACTION_CAPTURE_ENABLED", "true")
    monkeypatch.setenv("NUTRIMASTER_INTERACTION_CAPTURE_REQUIRE_CONSENT", "true")
    monkeypatch.setenv("NUTRIMASTER_INTERACTION_CAPTURE_DIR", str(tmp_path))

    recorder = InteractionRecorder.from_settings(Settings.from_env(env={}, project_root=tmp_path))
    session = recorder.start(
        user_id="user-1",
        session_id="session-1",
        client_turn_id="turn-1",
        query="hello",
        model_id="model",
        history=[],
        initial_messages=[{"role": "user", "content": "hello"}],
        use_personal=False,
        use_depth=False,
        capture_consent=False,
    )
    session.capture_event({"type": "text", "data": "answer"})
    session.finish()

    assert not (tmp_path / "interactions.jsonl").exists()


def test_interaction_recorder_writes_redacted_personal_tool_results(monkeypatch, tmp_path):
    from nutrimaster.agent.interaction_recording import InteractionRecorder
    from nutrimaster.config.settings import Settings

    monkeypatch.setenv("NUTRIMASTER_INTERACTION_CAPTURE_ENABLED", "true")
    monkeypatch.setenv("NUTRIMASTER_INTERACTION_CAPTURE_REQUIRE_CONSENT", "true")
    monkeypatch.setenv("NUTRIMASTER_INTERACTION_CAPTURE_DIR", str(tmp_path))
    monkeypatch.setenv("NUTRIMASTER_INTERACTION_INCLUDE_PERSONAL_CONTENT", "false")

    recorder = InteractionRecorder.from_settings(Settings.from_env(env={}, project_root=tmp_path))
    session = recorder.start(
        user_id="user-1",
        session_id="session-1",
        client_turn_id="turn-1",
        query="hello",
        model_id="model",
        history=[],
        initial_messages=[{"role": "user", "content": "hello"}],
        use_personal=True,
        use_depth=False,
        capture_consent=True,
    )
    session.capture_event({"type": "tool_call", "tool": "rag_search", "args": {"include_personal": True}})
    session.capture_event({"type": "tool_result", "tool": "rag_search", "content": "[1]\n来源: personal\nsecret"})
    session.capture_event({"type": "text", "data": "answer"})
    session.finish()

    rows = [json.loads(line) for line in (tmp_path / "interactions.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[0]["final"]["answer_text"] == "answer"
    assert rows[0]["final"]["tools_used"] == ["rag_search"]
    assert rows[0]["events"][1]["payload"]["content"] == "[redacted: personal library tool result]"
    assert rows[0]["user"]["user_hash"]
    assert "user_id" not in rows[0]["user"]


def test_interaction_feedback_is_recorded(monkeypatch, tmp_path):
    from nutrimaster.agent.interaction_recording import InteractionRecorder
    from nutrimaster.config.settings import Settings

    monkeypatch.setenv("NUTRIMASTER_INTERACTION_CAPTURE_ENABLED", "true")
    monkeypatch.setenv("NUTRIMASTER_INTERACTION_CAPTURE_DIR", str(tmp_path))

    recorder = InteractionRecorder.from_settings(Settings.from_env(env={}, project_root=tmp_path))
    payload = recorder.record_feedback(
        user_id="user-1",
        interaction_id="interaction-1",
        session_id="session-1",
        turn_id="turn-1",
        rating="up",
        comment="good",
    )

    rows = [json.loads(line) for line in (tmp_path / "feedback.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[0]["feedback_id"] == payload["feedback_id"]
    assert rows[0]["rating"] == "up"
