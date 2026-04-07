"""
个人知识库模块 — 用户 PDF 上传、解析、向量索引、检索

每个用户拥有独立的知识库（按 user_id 隔离），存储结构：
  personal_lib/{user_id}/
    pdfs/       — 上传的 PDF 原始文件
    index/      — 持久化的向量索引
      chunks.pkl       — 序列化的 chunk 列表（List[Dict]）
      embeddings.npy   — 对应的嵌入矩阵 (N, dim)
      manifest.json    — 文件元数据（页数、chunk 数、上传时间等）
"""
import json
import logging
import pickle
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from config import (
    PERSONAL_LIB_DIR,
    MAX_PDF_SIZE_MB,
    MAX_FILES_PER_USER,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)
from search.embedding_utils import get_embeddings, _build_headers

logger = logging.getLogger(__name__)


class PersonalLibrary:
    """
    用户个人 PDF 知识库：上传 → 解析 → 切块 → 嵌入 → 检索。

    每个实例绑定一个 user_id，对应一组独立的 PDF 文件和向量索引。
    """

    def __init__(self, user_id: str):
        """
        参数:
            user_id: 用户唯一标识（来自 Supabase auth）
        """
        self.user_id = user_id
        self.base_dir = PERSONAL_LIB_DIR / user_id  # 用户根目录
        self.pdf_dir = self.base_dir / "pdfs"        # PDF 存储目录
        self.index_dir = self.base_dir / "index"     # 索引存储目录

        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # ---- 用于 Jina API 调用的请求头 ----
        self._headers = _build_headers()

        # ---- 内存中的索引数据 ----
        self.chunks: List[Dict] = []                  # chunk 字典列表（含 content, metadata 等）
        self.embeddings: Optional[np.ndarray] = None   # 嵌入矩阵 (N, dim)
        self.manifest: Dict = {}                       # 文件元数据 {filename: {...}}

        self._load_index()

    # ------------------------------------------------------------------
    # 索引 I/O
    # ------------------------------------------------------------------
    def _load_index(self):
        """从磁盘加载已有索引（chunks + embeddings + manifest）"""
        chunks_file = self.index_dir / "chunks.pkl"
        emb_file = self.index_dir / "embeddings.npy"
        manifest_file = self.index_dir / "manifest.json"

        if chunks_file.exists() and emb_file.exists():
            with open(chunks_file, "rb") as f:
                self.chunks = pickle.load(f)
            self.embeddings = np.load(emb_file)
        if manifest_file.exists():
            with open(manifest_file, "r", encoding="utf-8") as f:
                self.manifest = json.load(f)

    def _save_index(self):
        """将内存中的索引持久化到磁盘"""
        with open(self.index_dir / "chunks.pkl", "wb") as f:
            pickle.dump(self.chunks, f)
        if self.embeddings is not None:
            np.save(self.index_dir / "embeddings.npy", self.embeddings)
        with open(self.index_dir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # PDF 处理
    # ------------------------------------------------------------------
    def upload_pdf(self, file_storage, filename: str) -> Dict:
        """保存 PDF → 提取文本 → 切块 → 向量化 → 追加索引"""
        # 检查文件数量限制
        if len(self.manifest) >= MAX_FILES_PER_USER:
            raise ValueError(f"最多上传 {MAX_FILES_PER_USER} 个文件")

        # 保存文件
        safe_name = filename.replace("/", "_").replace("\\", "_")
        pdf_path = self.pdf_dir / safe_name
        file_storage.save(str(pdf_path))

        # 检查大小
        size_mb = pdf_path.stat().st_size / (1024 * 1024)
        if size_mb > MAX_PDF_SIZE_MB:
            pdf_path.unlink()
            raise ValueError(f"文件过大 ({size_mb:.1f}MB)，最大 {MAX_PDF_SIZE_MB}MB")

        try:
            import fitz  # PyMuPDF
        except ImportError:
            pdf_path.unlink()
            raise ImportError("需要安装 PyMuPDF: pip install PyMuPDF")

        # 提取文本
        try:
            doc = fitz.open(str(pdf_path))
            pages_text = []
            for page in doc:
                text = page.get_text()
                if text.strip():
                    pages_text.append((page.number + 1, text))
            doc.close()
        except Exception as e:
            pdf_path.unlink()
            raise ValueError(f"PDF 解析失败: {e}")

        if not pages_text:
            pdf_path.unlink()
            raise ValueError("PDF 无法提取文本（可能是扫描件）")

        # 切块
        new_chunks = self._chunk_pages(safe_name, pages_text)

        # 向量化
        texts = [c["content"] for c in new_chunks]
        new_embeddings = self._get_embeddings(texts)

        # 追加到索引
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

    def _chunk_pages(self, filename: str, pages_text: List[tuple]) -> List[Dict]:
        """
        将 PDF 页面文本按固定窗口切分为 chunks。

        采用滑动窗口策略：窗口大小 = CHUNK_SIZE，步进 = CHUNK_SIZE - CHUNK_OVERLAP。
        相邻 chunk 之间有 CHUNK_OVERLAP 个字符重叠，确保跨窗口的句子不丢失。

        参数:
            filename:   PDF 文件名（作为 chunk 的 title 和 metadata）
            pages_text: [(page_number, page_text), ...] 页面文本列表

        返回:
            统一格式的 chunk 字典列表，每个 chunk 包含:
              source_type, title, content, url, score, metadata
        """
        chunks = []
        for page_num, text in pages_text:
            start = 0
            while start < len(text):
                end = start + CHUNK_SIZE
                chunk_text = text[start:end]
                if chunk_text.strip():
                    chunks.append({
                        "source_type": "personal",   # 标记来源为个人库
                        "title": filename,
                        "content": chunk_text.strip(),
                        "url": "",
                        "score": 0.0,                # 初始分数，检索时会更新
                        "metadata": {
                            "filename": filename,
                            "page": page_num,
                        },
                    })
                step = CHUNK_SIZE - CHUNK_OVERLAP    # 滑动步进
                start += max(step, 1)
        return chunks

    def _get_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """调用共享 Jina Embedding 工具获取文本向量（委托给 embedding_utils）"""
        return get_embeddings(texts, batch_size=batch_size, headers=self._headers)

    # ------------------------------------------------------------------
    # 文件管理
    # ------------------------------------------------------------------
    def delete_file(self, filename: str) -> bool:
        """
        删除指定 PDF 文件及其在索引中的所有 chunks。

        同时更新 manifest 和持久化索引。

        参数:
            filename: PDF 文件名

        返回:
            True 删除成功，False 文件不存在
        """
        if filename not in self.manifest:
            return False

        # ---- 删除 PDF 原始文件 ----
        pdf_path = self.pdf_dir / filename
        if pdf_path.exists():
            pdf_path.unlink()

        # ---- 从索引中移除该文件对应的所有 chunks ----
        keep_idx = [
            i for i, c in enumerate(self.chunks) if c["metadata"].get("filename") != filename
        ]
        self.chunks = [self.chunks[i] for i in keep_idx]
        if self.embeddings is not None and len(keep_idx) > 0:
            self.embeddings = self.embeddings[keep_idx]
        elif self.embeddings is not None:
            # 所有 chunk 都被删除，保留空矩阵（维持维度信息）
            self.embeddings = np.empty((0, self.embeddings.shape[1]))

        del self.manifest[filename]
        self._save_index()
        return True

    def rename_file(self, old_name: str, new_name: str) -> bool:
        if old_name not in self.manifest:
            return False
        safe_new = new_name.replace("/", "_").replace("\\", "_")

        # 重命名 PDF
        old_path = self.pdf_dir / old_name
        new_path = self.pdf_dir / safe_new
        if old_path.exists():
            old_path.rename(new_path)

        # 更新索引中的 filename 引用
        for c in self.chunks:
            if c["metadata"].get("filename") == old_name:
                c["metadata"]["filename"] = safe_new
                c["title"] = safe_new

        # 更新 manifest
        self.manifest[safe_new] = self.manifest.pop(old_name)
        self._save_index()
        return True

    def list_files(self) -> List[Dict]:
        return [
            {"filename": k, **v} for k, v in self.manifest.items()
        ]

    # ------------------------------------------------------------------
    # 搜索
    # ------------------------------------------------------------------
    def search(self, query_embedding: np.ndarray, top_k: int = 10) -> List[Dict]:
        """向量余弦相似度搜索个人库"""
        if self.embeddings is None or len(self.embeddings) == 0:
            return []

        scores = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding) + 1e-9
        )
        top_k = min(top_k, len(scores))
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for i in top_indices:
            item = dict(self.chunks[i])
            item["score"] = float(scores[i])
            results.append(item)
        return results
