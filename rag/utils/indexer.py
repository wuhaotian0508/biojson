"""
增量索引管理器 — manifest + sha256 + chunker_version 三重校验。

目标：
  - 启动时校验磁盘 JSON 数量 与 chunks.pkl 中的论文数是否一致
    不一致 → 打 WARNING 日志；
  - build_index_incremental() 只对新增 / 修改 / chunker 升级的文件
    重跑 embedding；未变化的部分复用老 chunks 与 embeddings，节省成本；
  - 原子写入：先写临时文件再 rename，避免中断导致索引损坏。

索引文件：
  - chunks.pkl          List[GeneChunk]           （全量 chunks）
  - embeddings.npy      np.ndarray (N, dim)       （对应向量）
  - manifest.json       { filename: {sha, chunker_version, n_chunks, start, end} }
  - relations.pkl       Dict[doi -> relations]    （可选，图扩展用）
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import pickle
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from utils.chunk_types import GeneChunk
from utils.chunker.schemas import CHUNKER_VERSION

logger = logging.getLogger("rag.indexer")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
    logger.addHandler(h)


def _texts_signature(texts):
    """对 texts 列表做一个轻量签名（首尾哈希 + 数量）用于 checkpoint 校验。"""
    h = hashlib.sha256()
    h.update(str(len(texts)).encode())
    # 只哈希前 5、中、后 5 条，防止太慢
    probe_idx = set()
    for i in range(min(5, len(texts))):
        probe_idx.add(i)
    if len(texts) > 10:
        probe_idx.add(len(texts) // 2)
    for i in range(max(0, len(texts) - 5), len(texts)):
        probe_idx.add(i)
    for i in sorted(probe_idx):
        h.update(f"|{i}|".encode())
        h.update(texts[i].encode("utf-8", errors="replace"))
    return h.hexdigest()


# ============================================================
# 文件辅助
# ============================================================
def sha256_of(path: Path, buf_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(buf_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _atomic_write_bytes(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def _atomic_write_pickle(path: Path, obj):
    _atomic_write_bytes(path, pickle.dumps(obj))


def _atomic_write_json(path: Path, obj):
    _atomic_write_bytes(path,
                        json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8"))


def _atomic_write_npy(path: Path, arr: np.ndarray):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", suffix=".npy", dir=str(path.parent))
    os.close(fd)
    np.save(tmp, arr)
    # np.save 自动追加 .npy
    tmp_npy = tmp if tmp.endswith(".npy") else tmp + ".npy"
    if not os.path.exists(tmp_npy):
        tmp_npy = tmp
    os.replace(tmp_npy, path)


# ============================================================
# Manifest
# ============================================================
class Manifest:
    """
    manifest.json 结构:
    {
      "chunker_version": "v2.2026-04",
      "files": {
        "10.xxx_nutri_plant_verified.json": {
          "sha": "...",
          "chunker_version": "v2.2026-04",
          "n_chunks": 5,
          "start": 1234,       # 在 chunks.pkl 中的起始下标
          "end": 1239          # 终止下标（exclusive）
        },
        ...
      }
    }
    """
    def __init__(self, path: Path):
        self.path = path
        self.files: Dict[str, dict] = {}
        self.chunker_version: str = CHUNKER_VERSION
        self.load()

    def load(self):
        if not self.path.exists():
            self.files = {}
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.files = data.get("files", {})
            self.chunker_version = data.get("chunker_version", CHUNKER_VERSION)
        except Exception as e:
            logger.warning(f"读取 manifest 失败，视为空 manifest: {e}")
            self.files = {}

    def save(self):
        _atomic_write_json(self.path, {
            "chunker_version": CHUNKER_VERSION,
            "files": self.files,
        })

    def needs_rebuild(self, filename: str, sha: str) -> bool:
        entry = self.files.get(filename)
        if entry is None:
            return True
        if entry.get("sha") != sha:
            return True
        if entry.get("chunker_version") != CHUNKER_VERSION:
            return True
        return False

    def get(self, filename: str) -> Optional[dict]:
        return self.files.get(filename)

    def set(self, filename: str, entry: dict):
        self.files[filename] = entry

    def pop(self, filename: str):
        self.files.pop(filename, None)


# ============================================================
# 索引构建
# ============================================================
class IncrementalIndexer:
    """
    增量索引。
    使用方式:
        indexer = IncrementalIndexer(index_dir, data_dir,
                                     embed_fn=lambda texts: np.ndarray)
        indexer.monitor_on_startup()           # 打印一致性检查
        chunks, embs = indexer.build_incremental(force=False)
    """
    def __init__(self, index_dir: Path, data_dir: Path,
                 embed_fn,                           # Callable[[List[str]], np.ndarray]
                 file_pattern: str = "*_nutri_plant_verified.json"):
        self.index_dir = Path(index_dir)
        self.data_dir = Path(data_dir)
        self.embed_fn = embed_fn
        self.file_pattern = file_pattern
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.chunks_path = self.index_dir / "chunks.pkl"
        self.embeds_path = self.index_dir / "embeddings.npy"
        self.manifest_path = self.index_dir / "manifest.json"
        self.relations_path = self.index_dir / "relations.pkl"
        self.manifest = Manifest(self.manifest_path)

    # ---------- 监控 ----------
    def monitor_on_startup(self):
        n_disk = len(list(self.data_dir.glob(self.file_pattern)))
        n_manifest = len(self.manifest.files)
        n_chunks = None
        if self.chunks_path.exists():
            try:
                with open(self.chunks_path, "rb") as f:
                    chunks = pickle.load(f)
                n_chunks = len(chunks)
            except Exception as e:
                logger.warning(f"读取 chunks.pkl 失败: {e}")

        logger.info(
            f"[monitor] data_dir={self.data_dir} 磁盘 verified JSON={n_disk}；"
            f"manifest 记录={n_manifest}；chunks.pkl={n_chunks} 条；"
            f"当前 chunker_version={CHUNKER_VERSION}；"
            f"manifest 版本={self.manifest.chunker_version}"
        )
        if n_disk == 0:
            logger.warning("[monitor] 数据目录下 0 个 verified JSON 文件！")
            return
        if n_manifest == 0 and self.chunks_path.exists():
            logger.warning(
                "[monitor] manifest 为空但 chunks.pkl 存在 —— "
                "索引可能是旧版本（无 manifest），建议 force=True 重建")
        diff = n_disk - n_manifest
        if diff > 0:
            logger.warning(
                f"[monitor] 磁盘比 manifest 多 {diff} 个 JSON —— "
                f"运行 build_incremental() 同步")
        elif diff < 0:
            logger.warning(
                f"[monitor] manifest 比磁盘多 {-diff} 个记录 —— "
                f"部分 JSON 已删除，build_incremental() 会自动清理")
        if (self.manifest.chunker_version and
                self.manifest.chunker_version != CHUNKER_VERSION):
            logger.warning(
                f"[monitor] chunker 版本变更 "
                f"({self.manifest.chunker_version} → {CHUNKER_VERSION}) —— "
                f"下次 build_incremental() 将全量重建")

    # ---------- 载入旧索引 ----------
    def _load_existing(self) -> Tuple[List[GeneChunk], Optional[np.ndarray]]:
        if not (self.chunks_path.exists() and self.embeds_path.exists()):
            return [], None
        try:
            with open(self.chunks_path, "rb") as f:
                chunks = pickle.load(f)
            embs = np.load(self.embeds_path)
            if len(chunks) != embs.shape[0]:
                logger.warning(
                    f"chunks.pkl ({len(chunks)}) 与 embeddings.npy "
                    f"({embs.shape[0]}) 数量不一致，忽略旧索引重建")
                return [], None
            return chunks, embs
        except Exception as e:
            logger.warning(f"加载旧索引失败: {e}")
            return [], None

    # ---------- 主入口 ----------
    def build_incremental(self, *, force: bool = False,
                          batch_embed_size: int = 32,
                          load_paper_fn=None):
        """
        增量构建索引。
        参数:
          force:             True → 丢弃旧索引全量重建。
          batch_embed_size:  embedding 批大小（由 embed_fn 内部再细分）。
          load_paper_fn:     Callable[Path] -> List[GeneChunk]
                             默认走 DataLoader.load_paper。
        """
        if load_paper_fn is None:
            from utils.data_loader import DataLoader
            load_paper_fn = DataLoader(self.data_dir).load_paper

        all_files = sorted(self.data_dir.glob(self.file_pattern))
        logger.info(f"扫描到 {len(all_files)} 个候选 JSON")

        # ---- 旧索引 ----
        if force:
            logger.info("force=True，丢弃旧索引")
            old_chunks, old_embs = [], None
            self.manifest.files = {}
        else:
            old_chunks, old_embs = self._load_existing()
            # 版本升级 → 强制全量
            if self.manifest.chunker_version and \
                    self.manifest.chunker_version != CHUNKER_VERSION:
                logger.warning(
                    "chunker_version 发生变化，触发全量重建")
                old_chunks, old_embs = [], None
                self.manifest.files = {}

        # ---- 分类 ----
        file_shas: Dict[str, str] = {}
        to_rebuild: List[Path] = []
        to_keep: List[str] = []
        disk_names = set()
        for p in all_files:
            disk_names.add(p.name)
            sha = sha256_of(p)
            file_shas[p.name] = sha
            if self.manifest.needs_rebuild(p.name, sha):
                to_rebuild.append(p)
            else:
                to_keep.append(p.name)

        # manifest 里有但磁盘上已删除的文件 → 需要清理
        to_remove = [name for name in self.manifest.files
                     if name not in disk_names]

        logger.info(
            f"待重建: {len(to_rebuild)}；复用: {len(to_keep)}；"
            f"从索引中移除: {len(to_remove)}")

        # ---- 复用 old chunks ----
        kept_chunks: List[GeneChunk] = []
        kept_embs_parts: List[np.ndarray] = []
        for name in to_keep:
            e = self.manifest.get(name)
            if not e:
                continue
            s, t = e["start"], e["end"]
            kept_chunks.extend(old_chunks[s:t])
            if old_embs is not None:
                kept_embs_parts.append(old_embs[s:t])

        # ---- 生成新 chunks ----
        new_chunks: List[GeneChunk] = []
        new_entries: List[Tuple[str, int, int]] = []  # (filename, rel_start, rel_end)
        for p in to_rebuild:
            try:
                cs = load_paper_fn(p) or []
            except Exception as ex:
                logger.error(f"加载 {p.name} 失败: {ex}")
                continue
            rel_start = len(new_chunks)
            new_chunks.extend(cs)
            rel_end = len(new_chunks)
            new_entries.append((p.name, rel_start, rel_end))
            if len(new_entries) % 100 == 0:
                logger.info(f"  已生成 chunks: {len(new_chunks)} "
                            f"（处理 {len(new_entries)}/{len(to_rebuild)} 篇）")

        # ---- embedding（带 checkpoint，支持断点续传）----
        new_embs: Optional[np.ndarray] = None
        checkpoint_dir = self.index_dir / ".embed_checkpoint"
        if new_chunks:
            logger.info(f"开始 embedding {len(new_chunks)} 个新 chunk ...")
            texts = [c.content for c in new_chunks]
            # 尝试加载 checkpoint
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            ckpt_embs_path = checkpoint_dir / "embs.npy"
            ckpt_meta_path = checkpoint_dir / "meta.json"
            done = 0
            partial_embs = None
            if ckpt_embs_path.exists() and ckpt_meta_path.exists():
                try:
                    meta = json.loads(ckpt_meta_path.read_text(encoding="utf-8"))
                    if meta.get("total") == len(texts) and meta.get("sig") == _texts_signature(texts):
                        partial_embs = np.load(ckpt_embs_path)
                        done = int(partial_embs.shape[0])
                        logger.info(f"发现 embedding checkpoint：已完成 {done}/{len(texts)}，断点续传")
                    else:
                        logger.info("embedding checkpoint 不匹配当前 chunks，丢弃重跑")
                except Exception as e:
                    logger.warning(f"读取 checkpoint 失败，忽略: {e}")
            if done < len(texts):
                remaining_texts = texts[done:]
                new_tail = self._embed_with_checkpoint(
                    remaining_texts, checkpoint_dir,
                    existing=partial_embs, total=len(texts),
                    sig=_texts_signature(texts),
                )
                if partial_embs is not None and len(partial_embs) > 0:
                    new_embs = np.concatenate([partial_embs, new_tail], axis=0)
                else:
                    new_embs = new_tail
            else:
                new_embs = partial_embs
            if not isinstance(new_embs, np.ndarray):
                new_embs = np.array(new_embs)
            if new_embs.shape[0] != len(new_chunks):
                raise RuntimeError(
                    f"embedding 返回数量不匹配: got {new_embs.shape[0]} "
                    f"expected {len(new_chunks)}")

        # ---- 拼接最终索引 ----
        final_chunks: List[GeneChunk] = list(kept_chunks)
        final_embs_parts: List[np.ndarray] = list(kept_embs_parts)
        new_start = len(final_chunks)
        final_chunks.extend(new_chunks)
        if new_embs is not None:
            final_embs_parts.append(new_embs)

        # ---- 重建 manifest（保留 kept，更新 rebuilt） ----
        new_manifest_files: Dict[str, dict] = {}
        # 先处理 kept
        cursor = 0
        for name in to_keep:
            old_entry = self.manifest.get(name)
            if not old_entry:
                continue
            n = old_entry["end"] - old_entry["start"]
            new_manifest_files[name] = {
                "sha": old_entry["sha"],
                "chunker_version": old_entry["chunker_version"],
                "n_chunks": n,
                "start": cursor,
                "end": cursor + n,
            }
            cursor += n
        # 再处理新生成的
        for (name, rs, re_) in new_entries:
            n = re_ - rs
            new_manifest_files[name] = {
                "sha": file_shas[name],
                "chunker_version": CHUNKER_VERSION,
                "n_chunks": n,
                "start": new_start + rs,
                "end": new_start + re_,
            }
        self.manifest.files = new_manifest_files

        # ---- 拼接 embeddings ----
        if final_embs_parts:
            final_embs = (np.concatenate(final_embs_parts, axis=0)
                          if len(final_embs_parts) > 1 else final_embs_parts[0])
        else:
            final_embs = None

        # 一致性校验
        if final_embs is not None:
            assert final_embs.shape[0] == len(final_chunks), \
                f"final_embs={final_embs.shape[0]} vs final_chunks={len(final_chunks)}"

        # ---- 持久化 ----
        _atomic_write_pickle(self.chunks_path, final_chunks)
        if final_embs is not None:
            _atomic_write_npy(self.embeds_path, final_embs)
        self.manifest.save()

        # 清理 checkpoint
        try:
            if checkpoint_dir.exists():
                for f in checkpoint_dir.iterdir():
                    f.unlink()
                checkpoint_dir.rmdir()
        except Exception:
            pass

        logger.info(
            f"索引构建完成: 总 chunk = {len(final_chunks)}；"
            f"embedding shape = "
            f"{final_embs.shape if final_embs is not None else 'None'}；"
            f"新增 embedding = {0 if new_embs is None else new_embs.shape[0]}；"
            f"文件记录数 = {len(self.manifest.files)}"
        )
        return final_chunks, final_embs

    # ---------- 带 checkpoint 的 embedding ----------
    def _embed_with_checkpoint(self, remaining_texts, checkpoint_dir, *,
                               existing, total, sig, batch_size=32,
                               flush_every_batches=10):
        """
        分批 embedding，每 flush_every_batches 批把当前累计向量写 checkpoint。
        existing: 已有 partial_embs（或 None）
        """
        ckpt_embs_path = checkpoint_dir / "embs.npy"
        ckpt_meta_path = checkpoint_dir / "meta.json"
        results_parts = []
        flushed = existing if existing is not None else np.zeros((0,), dtype=np.float32)
        batches_since_flush = 0
        for i in range(0, len(remaining_texts), batch_size):
            batch = remaining_texts[i:i + batch_size]
            emb = self.embed_fn(batch)
            if not isinstance(emb, np.ndarray):
                emb = np.array(emb)
            results_parts.append(emb)
            batches_since_flush += 1
            if batches_since_flush >= flush_every_batches:
                to_save = np.concatenate([flushed] + results_parts, axis=0) \
                    if flushed.size else np.concatenate(results_parts, axis=0)
                _atomic_write_npy(ckpt_embs_path, to_save)
                _atomic_write_json(ckpt_meta_path, {
                    "total": total, "done": int(to_save.shape[0]),
                    "sig": sig, "chunker_version": CHUNKER_VERSION,
                })
                logger.info(f"  [ckpt] 已保存 checkpoint: {to_save.shape[0]}/{total}")
                flushed = to_save
                results_parts = []
                batches_since_flush = 0
        # 末尾再保存一次
        if results_parts:
            to_save = np.concatenate([flushed] + results_parts, axis=0) \
                if flushed.size else np.concatenate(results_parts, axis=0)
            _atomic_write_npy(ckpt_embs_path, to_save)
            _atomic_write_json(ckpt_meta_path, {
                "total": total, "done": int(to_save.shape[0]),
                "sig": sig, "chunker_version": CHUNKER_VERSION,
            })
            flushed = to_save
        # 返回"新增部分"（不含 existing）
        existing_n = 0 if existing is None else int(existing.shape[0])
        return flushed[existing_n:]
