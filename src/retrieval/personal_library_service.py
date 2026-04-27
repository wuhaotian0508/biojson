from __future__ import annotations

from typing import Any


class PersonalLibraryService:
    """Stable service boundary for per-user personal library operations."""

    def __init__(self, library: Any):
        self._library = library

    def upload_pdf(self, file_storage: Any, filename: str) -> dict:
        return self._library.upload_pdf(file_storage, filename)

    def list_files(self) -> list[dict]:
        return self._library.list_files()

    def delete_file(self, filename: str) -> bool:
        return self._library.delete_file(filename)

    def rename_file(self, filename: str, new_name: str) -> bool:
        return self._library.rename_file(filename, new_name)

    def search(self, query_embedding: Any, top_k: int = 5) -> list[dict]:
        return self._library.search(query_embedding, top_k=top_k)
