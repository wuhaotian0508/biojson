from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RequestContext:
    user_input: str
    user_id: str | None = None
    model_id: str = ""
    history: list[dict] = field(default_factory=list)
    use_personal: bool = False
    use_depth: bool = False
