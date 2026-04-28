from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from typing import Mapping

from nutrimaster.web.responses import error_response
from nutrimaster.config.settings import Settings

SERVICE_NAME = "nutrimaster"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=SERVICE_NAME)
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve")
    serve.add_argument("--check-config", action="store_true")

    subparsers.add_parser("check-config")

    web = subparsers.add_parser("web")
    web.add_argument("--host")
    web.add_argument("--port", type=int)
    web.add_argument("--reload", action="store_true")

    extract = subparsers.add_parser("extract")
    extract.add_argument("--test")
    extract.add_argument("--workers", type=int)
    extract.add_argument("--rerun", action="store_true")

    return parser


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def _check_config(env: Mapping[str, str] | None = None, *, mode: str = "check-config") -> int:
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

    _print_json({"status": "ok", "service": SERVICE_NAME, "mode": mode})
    return 0


def _run_web(args: argparse.Namespace) -> int:
    import uvicorn

    settings = Settings.from_env()
    rag = settings.rag
    host = args.host or (rag.web_host if rag else "0.0.0.0")
    port = args.port or (rag.web_port if rag else 5000)
    reload = args.reload or (rag.debug if rag else False)
    uvicorn.run("nutrimaster.web.app:app", host=host, port=port, reload=reload)
    return 0


def _run_extract(args: argparse.Namespace) -> int:
    from nutrimaster.extraction.service import ExtractionService

    if args.rerun:
        os.environ["FORCE_RERUN"] = "1"
    result = ExtractionService().run(
        test=args.test,
        workers=args.workers,
        report_prefix="cli-extract",
    )
    _print_json(
        {
            "status": "ok",
            "files": result.files,
            "processed": result.processed,
            "failed": result.failed,
            "skipped": result.skipped,
            "stopped": result.stopped,
            "token_report": result.token_report,
        }
    )
    return 0


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.command == "serve" and args.check_config:
        return _check_config(env, mode="serve")
    if args.command == "check-config":
        return _check_config(env, mode="check-config")
    if args.command == "web":
        return _run_web(args)
    if args.command == "extract":
        return _run_extract(args)

    _build_parser().print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
