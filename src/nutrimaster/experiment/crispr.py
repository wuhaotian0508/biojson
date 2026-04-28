from __future__ import annotations

from typing import Any


def run_crispr_workflow(pipeline, genes: list[dict[str, Any]]) -> dict[str, str]:
    sops: dict[str, str] = {}
    errors: list[str] = []
    for event in pipeline.run_all_from_genes(genes):
        if event.get("type") == "result":
            sops = event.get("sops", {})
        elif event.get("type") == "error":
            errors.append(event.get("msg") or event.get("data") or "实验流程失败")
    if errors:
        raise RuntimeError("\n".join(errors))
    return sops
