from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from typing import Mapping

from server.responses import error_response
from shared.settings import Settings

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

    admin = subparsers.add_parser("admin")
    admin.add_argument("--host", default="0.0.0.0")
    admin.add_argument("--port", type=int)
    admin.add_argument("--debug", action="store_true")

    api = subparsers.add_parser("api")
    api.add_argument("--host", default="0.0.0.0")
    api.add_argument("--port", type=int, default=8000)
    api.add_argument("--reload", action="store_true")

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
    uvicorn.run("server.web:app", host=host, port=port, reload=reload)
    return 0


def _run_admin(args: argparse.Namespace) -> int:
    from admin.app import admin_bp, app

    settings = Settings.from_env()
    rag = settings.rag
    port = args.port or (rag.admin_port if rag else 5501)
    debug = args.debug or (rag.debug if rag else False)
    app.register_blueprint(admin_bp)
    app.run(host=args.host, port=port, debug=debug)
    return 0


def _run_api(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run("server.headless:app", host=args.host, port=args.port, reload=args.reload)
    return 0


def _run_extract(args: argparse.Namespace) -> int:
    from extractor.pipeline import main as pipeline_main

    if args.rerun:
        os.environ["FORCE_RERUN"] = "1"
    forwarded = ["nutrimaster extract"]
    if args.test is not None:
        forwarded.extend(["--test", args.test])
    if args.workers is not None:
        forwarded.extend(["--workers", str(args.workers)])

    old_argv = sys.argv
    sys.argv = forwarded
    try:
        pipeline_main()
    finally:
        sys.argv = old_argv
    return 0


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.command == "serve" and args.check_config:
        return _check_config(env, mode="serve")
    if args.command == "check-config":
        return _check_config(env, mode="check-config")
    if args.command == "web":
        return _run_web(args)
    if args.command == "admin":
        return _run_admin(args)
    if args.command == "api":
        return _run_api(args)
    if args.command == "extract":
        return _run_extract(args)

    _build_parser().print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
