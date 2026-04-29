from __future__ import annotations

import hashlib
import json
import os
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from nutrimaster.config.settings import Settings

PrivacyLevel = Literal["minimal", "standard", "full"]

SCHEMA_VERSION = "interaction.v1"
_REDACTED_PERSONAL_TOOL_RESULT = "[redacted: personal library tool result]"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value in (None, ""):
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int) -> int:
    if value in (None, ""):
        return default
    return int(value)


def _truncate(value: Any, limit: int) -> Any:
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + "\n...[truncated]"
    if isinstance(value, list):
        return [_truncate(item, limit) for item in value]
    if isinstance(value, dict):
        return {key: _truncate(item, limit) for key, item in value.items()}
    return value


def _contains_personal_source(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_personal_source(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_personal_source(item) for item in value)
    if not isinstance(value, str):
        return False
    text = value.lower()
    return "source_type': 'personal'" in text or '"source_type": "personal"' in text or "来源: personal" in text


@dataclass(frozen=True)
class InteractionCapturePolicy:
    enabled: bool
    require_consent: bool
    privacy_level: PrivacyLevel
    storage_dir: Path
    user_hash_salt: str = ""
    max_text_chars: int = 12000
    max_event_content_chars: int = 4000
    include_personal_content: bool = False
    include_system_prompt: bool = True

    @classmethod
    def from_settings(cls, settings: Settings) -> "InteractionCapturePolicy":
        env = os.environ
        storage_dir = Path(
            env.get(
                "NUTRIMASTER_INTERACTION_CAPTURE_DIR",
                settings.project_root / "data" / "interactions",
            )
        )
        privacy_level = env.get("NUTRIMASTER_INTERACTION_PRIVACY_LEVEL", "standard").strip().lower()
        if privacy_level not in {"minimal", "standard", "full"}:
            privacy_level = "standard"
        return cls(
            enabled=_as_bool(env.get("NUTRIMASTER_INTERACTION_CAPTURE_ENABLED"), True),
            require_consent=_as_bool(env.get("NUTRIMASTER_INTERACTION_CAPTURE_REQUIRE_CONSENT"), False),
            privacy_level=privacy_level,  # type: ignore[arg-type]
            storage_dir=storage_dir,
            user_hash_salt=env.get("NUTRIMASTER_INTERACTION_USER_HASH_SALT", settings.supabase_service_role_key),
            max_text_chars=_as_int(env.get("NUTRIMASTER_INTERACTION_MAX_TEXT_CHARS"), 12000),
            max_event_content_chars=_as_int(env.get("NUTRIMASTER_INTERACTION_MAX_EVENT_CHARS"), 4000),
            include_personal_content=_as_bool(env.get("NUTRIMASTER_INTERACTION_INCLUDE_PERSONAL_CONTENT"), False),
            include_system_prompt=_as_bool(env.get("NUTRIMASTER_INTERACTION_INCLUDE_SYSTEM_PROMPT"), True),
        )

    def public_config(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "require_consent": self.require_consent,
            "privacy_level": self.privacy_level,
        }


class InteractionRecorder:
    def __init__(self, policy: InteractionCapturePolicy):
        self.policy = policy
        self._lock = threading.Lock()

    @classmethod
    def from_settings(cls, settings: Settings) -> "InteractionRecorder":
        return cls(InteractionCapturePolicy.from_settings(settings))

    def start(
        self,
        *,
        user_id: str | None,
        session_id: str | None,
        client_turn_id: str | None,
        query: str,
        model_id: str,
        history: list[dict],
        initial_messages: list[dict],
        use_personal: bool,
        use_depth: bool,
        capture_consent: bool,
    ) -> "InteractionRecordingSession":
        interaction_id = str(uuid.uuid4())
        turn_id = client_turn_id or str(uuid.uuid4())
        active = self.policy.enabled and (capture_consent or not self.policy.require_consent)
        record = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "interaction",
            "interaction_id": interaction_id,
            "session_id": session_id or "",
            "turn_id": turn_id,
            "created_at": _utc_now(),
            "completed_at": None,
            "status": "running" if active else "skipped",
            "user": self._user_payload(user_id),
            "consent": {
                "granted": bool(capture_consent) or not self.policy.require_consent,
                "required": self.policy.require_consent,
                "privacy_level": self.policy.privacy_level,
            },
            "request": {
                "query": self._sanitize_text(query),
                "model_id": model_id or "",
                "use_personal": bool(use_personal),
                "use_depth": bool(use_depth),
                "history_count": len(history or []),
            },
            "messages": self._sanitize_messages(initial_messages, use_personal=use_personal),
            "events": [],
            "final": {
                "answer_text": "",
                "citations": [],
                "genes": [],
                "tools_used": [],
                "error": "",
            },
        }
        return InteractionRecordingSession(
            recorder=self,
            active=active,
            record=record,
            use_personal=use_personal,
        )

    def record_feedback(
        self,
        *,
        user_id: str | None,
        interaction_id: str,
        session_id: str | None,
        turn_id: str | None,
        rating: str,
        comment: str = "",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "feedback",
            "feedback_id": str(uuid.uuid4()),
            "interaction_id": interaction_id,
            "session_id": session_id or "",
            "turn_id": turn_id or "",
            "created_at": _utc_now(),
            "user": self._user_payload(user_id),
            "rating": rating,
            "comment": self._sanitize_text(comment),
            "tags": tags or [],
        }
        if self.policy.enabled:
            self._append_jsonl("feedback.jsonl", payload)
        return payload

    def _finish(self, record: dict[str, Any]) -> None:
        self._append_jsonl("interactions.jsonl", record)

    def _append_jsonl(self, filename: str, payload: dict[str, Any]) -> None:
        self.policy.storage_dir.mkdir(parents=True, exist_ok=True)
        path = self.policy.storage_dir / filename
        line = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        with self._lock:
            with path.open("a", encoding="utf-8") as file:
                file.write(line + "\n")

    def _user_payload(self, user_id: str | None) -> dict[str, str]:
        if not user_id:
            return {"user_hash": ""}
        digest = hashlib.sha256(f"{self.policy.user_hash_salt}:{user_id}".encode("utf-8")).hexdigest()
        payload = {"user_hash": digest}
        if self.policy.privacy_level == "full":
            payload["user_id"] = user_id
        return payload

    def _sanitize_messages(self, messages: list[dict], *, use_personal: bool) -> list[dict]:
        if self.policy.privacy_level == "minimal":
            return [{"role": msg.get("role", ""), "content_chars": len(str(msg.get("content", "")))} for msg in messages]
        output = []
        for msg in messages:
            if msg.get("role") == "system" and not self.policy.include_system_prompt:
                output.append({"role": "system", "content": "[redacted: system prompt]"})
                continue
            if use_personal and not self.policy.include_personal_content and msg.get("role") == "tool":
                output.append({**msg, "content": _REDACTED_PERSONAL_TOOL_RESULT})
                continue
            output.append(_truncate(dict(msg), self.policy.max_text_chars))
        return output

    def _sanitize_event(self, event: dict[str, Any], *, use_personal: bool) -> dict[str, Any]:
        event_type = event.get("type")
        sanitized = dict(event)
        if self.policy.privacy_level == "minimal":
            if event_type == "tool_call":
                return {"type": "tool_call", "tool": sanitized.get("tool")}
            if event_type == "tool_result":
                return {"type": "tool_result", "tool": sanitized.get("tool")}
            if event_type in {"text", "error"}:
                return {"type": event_type, "content_chars": len(str(sanitized.get("data", "")))}
            return sanitized

        if (
            event_type == "tool_result"
            and not self.policy.include_personal_content
            and (use_personal or _contains_personal_source(sanitized))
        ):
            sanitized["summary"] = _REDACTED_PERSONAL_TOOL_RESULT
            sanitized["content"] = _REDACTED_PERSONAL_TOOL_RESULT
        return _truncate(sanitized, self.policy.max_event_content_chars)

    def _sanitize_text(self, text: str) -> str:
        if self.policy.privacy_level == "minimal":
            return ""
        return _truncate(text or "", self.policy.max_text_chars)


class InteractionRecordingSession:
    def __init__(
        self,
        *,
        recorder: InteractionRecorder,
        active: bool,
        record: dict[str, Any],
        use_personal: bool,
    ):
        self.recorder = recorder
        self.active = active
        self.record = record
        self.use_personal = use_personal
        self._answer_parts: list[str] = []
        self._tools_used: list[str] = []

    @property
    def interaction_id(self) -> str:
        return str(self.record["interaction_id"])

    @property
    def turn_id(self) -> str:
        return str(self.record["turn_id"])

    def capture_event(self, event: dict[str, Any]) -> None:
        if not self.active:
            return
        event_type = event.get("type")
        self.record["events"].append(
            {
                "index": len(self.record["events"]),
                "created_at": _utc_now(),
                "payload": self.recorder._sanitize_event(event, use_personal=self.use_personal),
            }
        )
        if event_type == "tool_call":
            tool = str(event.get("tool") or "")
            if tool and tool not in self._tools_used:
                self._tools_used.append(tool)
        elif event_type == "text":
            self._answer_parts.append(str(event.get("data") or ""))
        elif event_type in {"citations", "sources"}:
            self.record["final"]["citations"] = _truncate(
                event.get("data") or [],
                self.recorder.policy.max_event_content_chars,
            )
        elif event_type == "genes_available":
            self.record["final"]["genes"] = event.get("genes") or []
        elif event_type == "error":
            self.record["final"]["error"] = str(event.get("data") or event.get("msg") or "")

    def finish(self, status: str = "completed") -> None:
        self.record["completed_at"] = _utc_now()
        self.record["status"] = status if self.active else self.record["status"]
        if not self.active:
            return
        self.record["final"]["answer_text"] = self.recorder._sanitize_text("".join(self._answer_parts))
        self.record["final"]["tools_used"] = list(self._tools_used)
        self.recorder._finish(self.record)


__all__ = [
    "InteractionCapturePolicy",
    "InteractionRecorder",
    "InteractionRecordingSession",
    "PrivacyLevel",
    "SCHEMA_VERSION",
]
