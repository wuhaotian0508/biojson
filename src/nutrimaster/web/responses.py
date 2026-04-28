from __future__ import annotations

from dataclasses import dataclass
from typing import Any


_SENSITIVE_DETAIL_KEYS = {"raw_exception", "traceback", "secret", "token", "authorization"}


@dataclass(frozen=True)
class ContractResponse:
    status_code: int
    body: dict[str, Any]


def _sanitize_details(details: dict[str, Any] | None) -> dict[str, Any]:
    if not details:
        return {}
    return {
        key: value
        for key, value in details.items()
        if key.lower() not in _SENSITIVE_DETAIL_KEYS
    }


def error_response(
    *,
    code: str,
    message: str,
    status_code: int,
    details: dict[str, Any] | None = None,
) -> ContractResponse:
    return ContractResponse(
        status_code=status_code,
        body={
            "error": {
                "code": code,
                "message": message,
                "details": _sanitize_details(details),
            }
        },
    )
