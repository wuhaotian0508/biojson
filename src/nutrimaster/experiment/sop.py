from __future__ import annotations


def format_sops(sops: dict[str, str]) -> str:
    return "\n\n".join(f"## {accession}\n{sop}" for accession, sop in sops.items())
