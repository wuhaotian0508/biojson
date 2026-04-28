from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from dotenv import dotenv_values


REQUIRED_REAL_SERVICE_KEYS = (
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "MODEL",
    "JINA_API_KEY",
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
)


def _find_dotenv(start: Path) -> Path | None:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate_dir in (current, *current.parents):
        candidate = candidate_dir / ".env"
        if candidate.exists():
            return candidate
    return None


def _default_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_env_with_dotenv(start: Path | None = None) -> dict[str, str]:
    values: dict[str, str] = {}
    dotenv_path = _find_dotenv(start or Path.cwd())
    if dotenv_path is not None:
        for key, value in dotenv_values(dotenv_path).items():
            if value is not None:
                values[key] = value
    values.update(os.environ)
    return values


def _as_int(source: Mapping[str, str], key: str, default: int) -> int:
    raw = source.get(key)
    if raw in (None, ""):
        return default
    return int(raw)


def _as_bool(source: Mapping[str, str], key: str, default: bool = False) -> bool:
    raw = source.get(key)
    if raw in (None, ""):
        return default
    return raw.lower() in {"true", "1", "yes", "on"}


@dataclass(frozen=True)
class RagSettings:
    """Runtime settings for RAG indexing, retrieval, personal library, and web."""

    data_dir: Path
    index_dir: Path
    personal_lib_dir: Path
    jina_embedding_url: str = "https://api.jina.ai/v1/embeddings"
    jina_rerank_url: str = "https://api.jina.ai/v1/rerank"
    embedding_model: str = "jina-embeddings-v3"
    rerank_model: str = "jina-reranker-v2-base-multilingual"
    top_k_retrieval: int = 20
    top_k_rerank: int = 10
    deep_top_k_retrieval: int = 20
    deep_top_k_rerank: int = 10
    chunk_size: int = 1500
    chunk_overlap: int = 200
    pubmed_max_results: int = 10
    max_pdf_size_mb: int = 50
    max_files_per_user: int = 20
    web_host: str = "0.0.0.0"
    web_port: int = 5000
    admin_port: int = 5501
    debug: bool = False

    @classmethod
    def from_env(cls, project_root: Path, env: Mapping[str, str]) -> "RagSettings":
        data_root = project_root / "data"
        corpus_root = data_root / "corpus"
        return cls(
            data_dir=Path(env.get("RAG_DATA_DIR", corpus_root)),
            index_dir=Path(env.get("RAG_INDEX_DIR", data_root / "index")),
            personal_lib_dir=Path(env.get("RAG_PERSONAL_LIB_DIR", data_root / "personal_lib")),
            top_k_retrieval=_as_int(env, "TOP_K_RETRIEVAL", 20),
            top_k_rerank=_as_int(env, "TOP_K_RERANK", 10),
            deep_top_k_retrieval=_as_int(env, "DEEP_TOP_K_RETRIEVAL", 20),
            deep_top_k_rerank=_as_int(env, "DEEP_TOP_K_RERANK", 10),
            chunk_size=_as_int(env, "CHUNK_SIZE", 1500),
            chunk_overlap=_as_int(env, "CHUNK_OVERLAP", 200),
            pubmed_max_results=_as_int(env, "PUBMED_MAX_RESULTS", 10),
            max_pdf_size_mb=_as_int(env, "MAX_PDF_SIZE_MB", 50),
            max_files_per_user=_as_int(env, "MAX_FILES_PER_USER", 20),
            web_host=env.get("WEB_HOST", "0.0.0.0"),
            web_port=_as_int(env, "WEB_PORT", 5000),
            admin_port=_as_int(env, "ADMIN_PORT", 5501),
            debug=_as_bool(env, "DEBUG", False),
        )


@dataclass(frozen=True)
class LlmSettings:
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    fallback_api_key: str = ""
    fallback_base_url: str = ""
    fallback_model: str = ""


@dataclass(frozen=True)
class AuthSettings:
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_anon_key: str = ""
    site_url: str = ""


@dataclass(frozen=True)
class EmailSettings:
    smtp_user: str = "nutrimaster@163.com"
    smtp_password: str = ""
    smtp_host: str = "smtp.163.com"
    smtp_port: int = 465
    smtp_from_name: str = "NutriMaster"


@dataclass(frozen=True)
class Settings:
    """Typed runtime settings shared by NutriMaster services."""

    project_root: Path
    openai_api_key: str = ""
    openai_base_url: str = ""
    model: str = ""
    jina_api_key: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_anon_key: str = ""
    site_url: str = ""
    fallback_api_key: str = ""
    fallback_base_url: str = ""
    fallback_model: str = ""
    smtp_user: str = "nutrimaster@163.com"
    smtp_password: str = ""
    smtp_host: str = "smtp.163.com"
    smtp_port: int = 465
    smtp_from_name: str = "NutriMaster"
    llm: LlmSettings = field(default_factory=LlmSettings)
    auth: AuthSettings = field(default_factory=AuthSettings)
    email: EmailSettings = field(default_factory=EmailSettings)
    rag: RagSettings | None = None

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        project_root: Path | None = None,
    ) -> "Settings":
        source = _load_env_with_dotenv(project_root) if env is None else env
        default_root = project_root or _default_project_root()
        project_root = Path(source.get("NUTRIMASTER_ROOT", default_root))
        llm = LlmSettings(
            api_key=source.get("OPENAI_API_KEY", ""),
            base_url=source.get("OPENAI_BASE_URL", ""),
            model=source.get("MODEL", ""),
            fallback_api_key=source.get("FALLBACK_API_KEY", ""),
            fallback_base_url=source.get("FALLBACK_BASE_URL", ""),
            fallback_model=source.get("FALLBACK_MODEL", ""),
        )
        auth = AuthSettings(
            supabase_url=source.get("SUPABASE_URL", ""),
            supabase_service_role_key=source.get("SUPABASE_SERVICE_ROLE_KEY", ""),
            supabase_anon_key=source.get("NEXT_PUBLIC_SUPABASE_ANON_KEY", ""),
            site_url=source.get("SITE_URL", ""),
        )
        email = EmailSettings(
            smtp_user=source.get("SMTP_USER", "nutrimaster@163.com"),
            smtp_password=source.get("SMTP_PASSWORD", ""),
            smtp_host=source.get("SMTP_HOST", "smtp.163.com"),
            smtp_port=_as_int(source, "SMTP_PORT", 465),
            smtp_from_name=source.get("SMTP_FROM_NAME", "NutriMaster"),
        )
        return cls(
            project_root=project_root,
            openai_api_key=llm.api_key,
            openai_base_url=llm.base_url,
            model=llm.model,
            jina_api_key=source.get("JINA_API_KEY", ""),
            supabase_url=auth.supabase_url,
            supabase_service_role_key=auth.supabase_service_role_key,
            supabase_anon_key=auth.supabase_anon_key,
            site_url=auth.site_url,
            fallback_api_key=llm.fallback_api_key,
            fallback_base_url=llm.fallback_base_url,
            fallback_model=llm.fallback_model,
            smtp_user=email.smtp_user,
            smtp_password=email.smtp_password,
            smtp_host=email.smtp_host,
            smtp_port=email.smtp_port,
            smtp_from_name=email.smtp_from_name,
            llm=llm,
            auth=auth,
            email=email,
            rag=RagSettings.from_env(project_root, source),
        )

    def missing_real_service_keys(self) -> list[str]:
        values = {
            "OPENAI_API_KEY": self.openai_api_key,
            "OPENAI_BASE_URL": self.openai_base_url,
            "MODEL": self.model,
            "JINA_API_KEY": self.jina_api_key,
            "SUPABASE_URL": self.supabase_url,
            "SUPABASE_SERVICE_ROLE_KEY": self.supabase_service_role_key,
        }
        return [key for key in REQUIRED_REAL_SERVICE_KEYS if not values[key]]
