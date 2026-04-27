from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from typing import Mapping

from server.responses import error_response
from shared.settings import Settings


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="biojson")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve")
    serve.add_argument("--check-config", action="store_true")

    return parser


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.command == "serve" and args.check_config:
        settings = Settings.from_env(env)
        missing = settings.missing_real_service_keys()
        if missing:
            response = error_response(
                code="missing_real_service_config",
                message="NutriMaster real-service configuration is incomplete",
                status_code=2,
                details={"missing": missing},
            )
            _print_json(response.body)
            return response.status_code

        _print_json({"status": "ok", "service": "biojson", "mode": "serve"})
        return 0

    _build_parser().print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
