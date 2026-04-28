from __future__ import annotations

import json
import pickle
import re
import time
from pathlib import Path
from typing import Any

import numpy as np
import requests

from nutrimaster.config.settings import RagSettings, Settings

_SAFE_FILENAME_RE = re.compile(r"[^\w\u4e00-\u9fff\-. ]", re.UNICODE)


def sanitize_filename(name: str) -> str:
    name = Path(name).name
    name = _SAFE_FILENAME_RE.sub("_", name)
    name = re.sub(r"[_ ]{2,}", "_", name).strip("_. ")
    return name or f"upload_{int(time.time())}.pdf"


class PersonalLibrary:
    def __init__(
        self,
        user_id: str,
        *,
        rag_settings: RagSettings | None = None,
        embed_texts=None,
    ):
        self.user_id = user_id
        self.rag_settings = rag_settings or Settings.from_env().rag
        if self.rag_settings is None:
            raise RuntimeError("RAG settings failed to initialize")
        self._embed_texts = embed_texts or self._default_embed_texts
        self.base_dir = self.rag_settings.personal_lib_dir / user_id
        self.pdf_dir = self.base_dir / "pdfs"
        self.index_dir = self.base_dir / "index"
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.chunks: list[dict[str, Any]] = []
        self.embeddings: np.ndarray | None = None
        self.manifest: dict[str, Any] = {}
        self._load_index()

    def _load_index(self):
        chunks_file = self.index_dir / "chunks.pkl"
        embeddings_file = self.index_dir / "embeddings.npy"
        manifest_file = self.index_dir / "manifest.json"
        if chunks_file.exists() and embeddings_file.exists():
            with chunks_file.open("rb") as file:
                self.chunks = pickle.load(file)
            self.embeddings = np.load(embeddings_file)
        if manifest_file.exists():
            self.manifest = json.loads(manifest_file.read_text(encoding="utf-8"))

    def _save_index(self):
        with (self.index_dir / "chunks.pkl").open("wb") as file:
            pickle.dump(self.chunks, file)
        if self.embeddings is not None:
            np.save(self.index_dir / "embeddings.npy", self.embeddings)
        (self.index_dir / "manifest.json").write_text(
            json.dumps(self.manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def upload_pdf(self, file_storage, filename: str) -> dict:
        if len(self.manifest) >= self.rag_settings.max_files_per_user:
            raise ValueError(f"最多上传 {self.rag_settings.max_files_per_user} 个文件")
        safe_name = sanitize_filename(filename)
        pdf_path = self.pdf_dir / safe_name
        file_storage.save(str(pdf_path))
        size_mb = pdf_path.stat().st_size / (1024 * 1024)
        if size_mb > self.rag_settings.max_pdf_size_mb:
            pdf_path.unlink()
            raise ValueError(f"文件过大 ({size_mb:.1f}MB)，最大 {self.rag_settings.max_pdf_size_mb}MB")
        pages_text = self._extract_pdf_text(pdf_path)
        if not pages_text:
            pdf_path.unlink()
            raise ValueError("PDF 无法提取文本（可能是扫描件）")
        new_chunks = self._chunk_pages(safe_name, pages_text)
        new_embeddings = self._embed_texts([chunk["content"] for chunk in new_chunks])
        self.chunks.extend(new_chunks)
        if self.embeddings is not None and len(self.embeddings) > 0:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])
        else:
            self.embeddings = new_embeddings
        self.manifest[safe_name] = {
            "num_pages": len(pages_text),
            "num_chunks": len(new_chunks),
            "upload_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "size_mb": round(size_mb, 2),
        }
        self._save_index()
        return self.manifest[safe_name]

    @staticmethod
    def _extract_pdf_text(pdf_path: Path) -> list[tuple[int, str]]:
        try:
            import fitz
        except ImportError as exc:
            raise ImportError("需要安装 PyMuPDF: pip install PyMuPDF") from exc
        try:
            doc = fitz.open(str(pdf_path))
            pages = [
                (page.number + 1, text)
                for page in doc
                if (text := page.get_text()).strip()
            ]
            doc.close()
            return pages
        except Exception as exc:
            raise ValueError(f"PDF 解析失败: {exc}") from exc

    def _chunk_pages(self, filename: str, pages_text: list[tuple[int, str]]) -> list[dict]:
        chunks = []
        step = max(self.rag_settings.chunk_size - self.rag_settings.chunk_overlap, 1)
        for page_num, text in pages_text:
            start = 0
            while start < len(text):
                chunk_text = text[start:start + self.rag_settings.chunk_size]
                if chunk_text.strip():
                    chunks.append(
                        {
                            "source_type": "personal",
                            "title": filename,
                            "content": chunk_text.strip(),
                            "url": "",
                            "score": 0.0,
                            "metadata": {"filename": filename, "page": page_num},
                        }
                    )
                start += step
        return chunks

    def delete_file(self, filename: str) -> bool:
        if filename not in self.manifest:
            return False
        pdf_path = self.pdf_dir / filename
        if pdf_path.exists():
            pdf_path.unlink()
        keep = [
            index
            for index, chunk in enumerate(self.chunks)
            if chunk["metadata"].get("filename") != filename
        ]
        self.chunks = [self.chunks[index] for index in keep]
        if self.embeddings is not None:
            self.embeddings = self.embeddings[keep] if keep else np.empty((0, self.embeddings.shape[1]))
        del self.manifest[filename]
        self._save_index()
        return True

    def rename_file(self, old_name: str, new_name: str) -> bool:
        if old_name not in self.manifest:
            return False
        safe_new = sanitize_filename(new_name)
        old_path = self.pdf_dir / old_name
        if old_path.exists():
            old_path.rename(self.pdf_dir / safe_new)
        for chunk in self.chunks:
            if chunk["metadata"].get("filename") == old_name:
                chunk["metadata"]["filename"] = safe_new
                chunk["title"] = safe_new
        self.manifest[safe_new] = self.manifest.pop(old_name)
        self._save_index()
        return True

    def list_files(self) -> list[dict]:
        return [{"filename": filename, **meta} for filename, meta in self.manifest.items()]

    def search(self, query_embedding: np.ndarray, top_k: int = 10) -> list[dict]:
        if self.embeddings is None or len(self.embeddings) == 0:
            return []
        scores = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding) + 1e-9
        )
        indices = np.argsort(scores)[::-1][: min(top_k, len(scores))]
        results = []
        for index in indices:
            item = dict(self.chunks[int(index)])
            item["score"] = float(scores[int(index)])
            results.append(item)
        return results

    def _default_embed_texts(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        api_key = Settings.from_env().jina_api_key
        if not api_key:
            raise RuntimeError("JINA_API_KEY is required")
        response = requests.post(
            self.rag_settings.jina_embedding_url,
            json={
                "model": self.rag_settings.embedding_model,
                "input": texts,
                "task": "retrieval.passage",
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60,
        )
        response.raise_for_status()
        return np.array([item["embedding"] for item in response.json()["data"]])


__all__ = ["PersonalLibrary", "sanitize_filename"]
