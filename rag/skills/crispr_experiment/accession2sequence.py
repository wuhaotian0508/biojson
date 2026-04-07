"""
Step 2: Accession → FASTA 序列

功能：读取 accession 文件，从 NCBI Entrez efetch 下载对应的 FASTA 核酸序列。

输入：accession_file — Step 1 生成的 TSV 文件（3 列：gene, species, accession）
     work_dir — 工作目录（Path）
输出：FASTA 文件路径（Path）
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# ---- NCBI Entrez efetch 接口地址 ----
_ENTREZ_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
# ---- 请求标识 ----
_ENTREZ_EMAIL = "biojson_rag@example.com"
_MAX_RETRIES = 3


def _has_env_proxy() -> bool:
    """
    检测当前环境是否配置了代理服务器。

    检查常见的代理环境变量（大小写两种格式均检查）。
    返回 True 表示至少有一个代理变量被设置（非空）。

    用途：决定下载时是否启用系统代理，以应对网络受限的服务器环境。
    在有代理的环境中，优先尝试通过代理请求；若代理连接失败则回退到直连。
    """
    return any(
        os.getenv(name)
        for name in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY")
    )


def _build_session(use_env_proxy: bool) -> requests.Session:
    """
    构建配置好的 HTTP 请求会话。

    参数:
        use_env_proxy: True 表示使用系统环境变量中的代理；
                       False 表示禁用代理，直接连接目标服务器

    返回:
        已配置 User-Agent 等请求头的 requests.Session 对象

    注意：
        - trust_env=False 时 requests 会忽略 http_proxy/https_proxy 环境变量，
          实现"强制直连"效果
        - Accept-Encoding: identity 禁用压缩，避免某些 NCBI 响应解压失败
        - Connection: close 防止连接复用导致的 EOF 错误
    """
    session = requests.Session()
    session.trust_env = use_env_proxy   # trust_env: 是否信任环境变量中的代理设置
    session.headers.update({
        "User-Agent": "biojson_rag/1.0",          # 标识请求来源（NCBI 要求有 User-Agent）
        "Accept-Encoding": "identity",             # 禁用 gzip/br 压缩，提高稳定性
        "Connection": "close",                     # 每次请求后关闭连接，避免超时积压
    })
    return session


def _fetch_fasta_text(acc: str, params: dict) -> str:
    """
    从 NCBI Entrez efetch 下载单个 accession 的 FASTA 文本。

    实现了"代理优先，失败则直连"的容错策略：
    - 若环境中配置了代理，先尝试通过代理下载，失败后再尝试直连
    - 若无代理，直接使用系统默认连接方式

    每种连接模式下最多重试 _MAX_RETRIES 次，重试间隔随次数线性增长
    （第 1 次失败等 1 秒，第 2 次失败等 2 秒）。

    参数:
        acc:    accession 编号（仅用于日志输出，不影响请求）
        params: 传给 NCBI efetch 的 URL 查询参数字典，应包含
                db、id、rettype、retmode 等字段

    返回:
        FASTA 格式文本字符串（已去除首尾空白）

    异常:
        最后一次请求的 requests.RequestException（所有模式均失败时）
        ValueError: 当代理模式列表为空时（理论上不会发生）
    """
    last_error = None
    # proxy_modes: 要尝试的连接模式列表
    # 有代理时先尝试代理（True），失败后再尝试直连（False）
    # 无代理时只有直连模式（True，trust_env=True 但无代理变量，等同于直连）
    proxy_modes = [True, False] if _has_env_proxy() else [True]

    for use_env_proxy in proxy_modes:
        mode_name = "env-proxy" if use_env_proxy else "direct"   # 仅用于日志
        session = _build_session(use_env_proxy)
        try:
            for attempt in range(1, _MAX_RETRIES + 1):
                # attempt: 当前重试次数（从 1 开始）
                try:
                    # timeout=(10, 30)：连接超时 10 秒，读取超时 30 秒
                    r = session.get(_ENTREZ_EFETCH_URL, params=params, timeout=(10, 30))
                    r.raise_for_status()   # 4xx/5xx 状态码抛出异常
                    return r.text.strip()
                except requests.exceptions.RequestException as exc:
                    last_error = exc       # last_error: 最近一次异常，最终失败时重新抛出
                    logger.warning(
                        "accession %s 下载失败 (%s attempt %d/%d): %s",
                        acc, mode_name, attempt, _MAX_RETRIES, exc,
                    )
                    if attempt < _MAX_RETRIES:
                        time.sleep(attempt)   # 线性退避：第 n 次失败后等 n 秒
        finally:
            session.close()   # 确保 session 被关闭，释放底层 TCP 连接

    if last_error is not None:
        raise last_error
    raise ValueError(f"未能下载 accession {acc} 的序列")


def run_accession2sequence(accession_file: Path, work_dir: Path) -> Path:
    """
    从 NCBI 下载基因序列。

    逐行读取 accession 文件，对每个有效 accession 调用 NCBI efetch
    下载 FASTA 格式序列，合并写入一个 FASTA 文件。
    每次请求间隔 0.34 秒以遵守 NCBI 速率限制。

    参数:
        accession_file: Step 1 生成的 accession TSV 文件
        work_dir: 临时工作目录

    返回:
        FASTA 文件路径

    异常:
        ValueError: 当没有有效 accession 可供下载，或未能下载到任何序列时抛出
    """
    fasta_file = work_dir / "sequence.fas"

    # ---- 从 accession 文件中提取有效 accession ----
    accessions = []
    with open(accession_file, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            # 第 3 列为 accession，跳过空值
            if len(parts) >= 3 and parts[2]:
                accessions.append(parts[2])

    if not accessions:
        raise ValueError("没有有效的 accession 可供下载序列")

    # ---- 逐个下载 FASTA 序列 ----
    with open(fasta_file, "w") as out_f:
        for acc in accessions:
            params = {
                "db": "nuccore",          # 核酸数据库
                "id": acc,                # accession 编号
                "rettype": "fasta",       # 返回 FASTA 格式
                "retmode": "text",        # 纯文本模式
                "email": _ENTREZ_EMAIL,   # NCBI 要求的邮箱标识
                "tool": "biojson_rag",    # 工具标识
            }
            try:
                text = _fetch_fasta_text(acc, params)
            except requests.exceptions.RequestException as exc:
                logger.warning("accession %s 下载异常，跳过: %s", acc, exc)
                continue

            # 验证返回的确实是 FASTA 格式（以 > 开头）
            if not text.startswith(">"):
                logger.warning("accession %s 返回非 FASTA 格式，跳过", acc)
                continue

            # 简化 FASTA header 为 >accession 便于后续处理
            lines = text.splitlines()
            lines[0] = f">{acc}"
            out_f.write("\n".join(lines) + "\n")

            # NCBI 速率限制：每秒不超过 3 次请求
            time.sleep(0.34)

    # ---- 检查是否成功下载到序列 ----
    if fasta_file.stat().st_size == 0:
        raise ValueError("未能下载到任何基因序列")

    return fasta_file
