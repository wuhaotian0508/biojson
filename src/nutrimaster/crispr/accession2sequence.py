from __future__ import annotations

import logging
import os
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

_ENTREZ_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
_ENTREZ_EMAIL = "nutrimaster_rag@example.com"
_MAX_RETRIES = 3


def _has_env_proxy() -> bool:
    return any(
        os.getenv(name)
        for name in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY")
    )


def _build_session(use_env_proxy: bool) -> requests.Session:
    session = requests.Session()
    session.trust_env = use_env_proxy
    session.headers.update(
        {
            "User-Agent": "nutrimaster_rag/1.0",
            "Accept-Encoding": "identity",
            "Connection": "close",
        }
    )
    return session


def _fetch_fasta_text(accession: str, params: dict) -> str:
    last_error = None
    for use_env_proxy in ([True, False] if _has_env_proxy() else [True]):
        mode = "env-proxy" if use_env_proxy else "direct"
        session = _build_session(use_env_proxy)
        try:
            for attempt in range(1, _MAX_RETRIES + 1):
                try:
                    response = session.get(_ENTREZ_EFETCH_URL, params=params, timeout=(10, 30))
                    response.raise_for_status()
                    return response.text.strip()
                except requests.exceptions.RequestException as exc:
                    last_error = exc
                    logger.warning(
                        "accession %s download failed (%s attempt %d/%d): %s",
                        accession,
                        mode,
                        attempt,
                        _MAX_RETRIES,
                        exc,
                    )
                    if attempt < _MAX_RETRIES:
                        time.sleep(attempt)
        finally:
            session.close()
    if last_error is not None:
        raise last_error
    raise ValueError(f"未能下载 accession {accession} 的序列")


def run_accession2sequence(accession_file: Path, work_dir: Path) -> Path:
    fasta_file = work_dir / "sequence.fas"
    accessions = []
    with accession_file.open(encoding="utf-8") as file:
        for line in file:
            parts = line.strip().split("\t")
            if len(parts) >= 3 and parts[2]:
                accessions.append(parts[2])
    if not accessions:
        raise ValueError("没有有效的 accession 可供下载序列")
    with fasta_file.open("w", encoding="utf-8") as output:
        for accession in accessions:
            params = {
                "db": "nuccore",
                "id": accession,
                "rettype": "fasta",
                "retmode": "text",
                "email": _ENTREZ_EMAIL,
                "tool": "nutrimaster_rag",
            }
            try:
                text = _fetch_fasta_text(accession, params)
            except requests.exceptions.RequestException as exc:
                logger.warning("accession %s download failed, skipping: %s", accession, exc)
                continue
            if not text.startswith(">"):
                logger.warning("accession %s returned non-FASTA content, skipping", accession)
                continue
            lines = text.splitlines()
            lines[0] = f">{accession}"
            output.write("\n".join(lines) + "\n")
            time.sleep(0.34)
    if fasta_file.stat().st_size == 0:
        raise ValueError("未能下载到任何基因序列")
    return fasta_file


__all__ = ["run_accession2sequence"]
