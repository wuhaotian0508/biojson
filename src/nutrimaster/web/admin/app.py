"""
 NutriMaster Admin Panel 后端（Flask Blueprint，挂载在主 Web 服务下）

功能概述：
  1. ZIP 上传 → 递归解压 .md 到 src/nutrimaster/extraction/input/，自动去重
  2. Pipeline 预览 / 批量运行（ThreadPoolExecutor 并行）/ 停止
  3. SSE 流式推送处理进度
  4. Console Output 实时查看 pipeline 的 print 输出
  5. 在线编辑 prompt 和 schema 文件
  6. 可调参数：temperature、verify 批次大小、并行 worker 数

认证：Supabase Bearer Token + ADMIN_EMAIL 邮箱白名单
"""

import json
import io
import os
import queue
import threading
import zipfile
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from io import BytesIO
from pathlib import Path

from flask import Response, jsonify, request, send_from_directory

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  环境变量设置 — 必须在 import nutrimaster.extraction 之前完成                            ║
# ║  因为 src/nutrimaster/extraction/config.py 在 import 时就读取 env，之后无法再改              ║
# ╚══════════════════════════════════════════════════════════════════════════╝

from nutrimaster.config.settings import Settings

SETTINGS = Settings.from_env()
REPO_ROOT = SETTINGS.project_root

# 设置 extractor 需要的关键路径（setdefault 不会覆盖已存在的值）
os.environ.setdefault("JSON_DIR", str(SETTINGS.rag.data_dir))
EXTRACTION_ROOT = REPO_ROOT / "src" / "nutrimaster" / "extraction"
os.environ.setdefault("PROMPT_PATH", str(EXTRACTION_ROOT / "prompts" / "nutri_gene_prompt_v5.txt"))
os.environ.setdefault("SCHEMA_PATH", str(EXTRACTION_ROOT / "prompts" / "nutri_gene_schema_v5.json"))
os.environ.setdefault("MD_DIR", str(EXTRACTION_ROOT / "input"))

# 加载 .env 文件（API key、Supabase 等配置）
from dotenv import load_dotenv
load_dotenv(REPO_ROOT / ".env")

# Supabase 客户端（用于服务端验证 token）
from supabase import create_client

# extractor 模块导入（此时 env 已就绪）
from nutrimaster.extraction.config import INPUT_DIR, ensure_dirs
from nutrimaster.extraction.pipeline import process_one_paper, run_pipeline_batch, save_token_report
from nutrimaster.extraction.token_tracker import TokenTracker

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Flask App 初始化                                                         ║
# ╚══════════════════════════════════════════════════════════════════════════╝

from flask import Blueprint

# Blueprint 版本（供 nutrimaster.web.app 集成使用）
# url_prefix 由注册方决定，这里不设前缀
admin_bp = Blueprint(
    "admin",
    __name__,
    static_folder="static",
    static_url_path="/static",
)

# 下方所有路由都注册到 admin_bp 上，由主 FastAPI app 挂载。

# 管理员邮箱白名单（逗号分隔，支持多个邮箱）
ADMIN_EMAILS = {e.strip() for e in os.getenv("ADMIN_EMAIL", "").split(",") if e.strip()}

# Supabase 配置
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# 常用路径
DATA_DIR = SETTINGS.rag.data_dir                  # verified JSON 最终存放目录
PROMPT_PATH = Path(os.environ["PROMPT_PATH"])     # prompt 文件路径
SCHEMA_PATH = Path(os.environ["SCHEMA_PATH"])     # schema 文件路径

# 初始化 Supabase 服务端客户端（用 service_role_key 验证用户 token）
supabase = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    except Exception as e:
        print(f"⚠️  Supabase 初始化失败 ({e})，认证功能不可用")

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Pipeline 参数默认值 & 允许范围                                            ║
# ║  前端 Settings 面板可调，通过 POST body 传入                               ║
# ╚══════════════════════════════════════════════════════════════════════════╝

PIPELINE_DEFAULTS = {
    "temperature": 0.7,          # 提取 API 的温度参数（0=确定性，1=创造性）
    "verify_batch_genes": 12,    # 每批验证多少个基因（越大单次 API 处理越多）
    "max_workers": 32,           # 并行处理论文数（ThreadPoolExecutor 线程数）
}

PIPELINE_LIMITS = {
    "temperature":       (0.0, 1.0),
    "verify_batch_genes": (1, 50),
    "max_workers":        (1, 64),    # 最大 64 并行
}

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Pipeline 运行状态（模块级，线程安全）                                       ║
# ║  同一时间只允许一个 pipeline 实例运行                                        ║
# ╚══════════════════════════════════════════════════════════════════════════╝

_lock = threading.Lock()
pipeline_state = {
    "running": False,          # 是否有 pipeline 正在运行
    "stop_requested": False,   # 用户是否请求停止
    "total": 0,                # 本次运行总文件数
    "done": 0,                 # 已完成文件数
    "current_file": "",        # 当前正在处理的文件名
    "events": queue.Queue(),   # SSE 事件队列（元组：(event_type, data_dict)）
    "thread": None,            # 后台线程引用
    "output": "",              # 最近一次运行的 console 输出（最后 5000 字符）
    "_tee": None,              # 运行中的 _TeeWriter 实例（用于实时读取输出）
    "tracker": None,           # 当前运行的 TokenTracker 实例（供实时查询）
}

_index_refresh_handler: Callable[[Path, bool], None] | None = None


def configure_index_refresh(handler: Callable[[Path, bool], None] | None) -> None:
    """Inject the host app's retriever refresh function.

    Standalone admin falls back to constructing its own retriever, while the
    integrated FastAPI app passes its live retriever so new corpus files are
    visible to the current query process after indexing.
    """
    global _index_refresh_handler
    _index_refresh_handler = handler


def _refresh_index(data_dir: Path, *, force: bool = False) -> None:
    if _index_refresh_handler is not None:
        _index_refresh_handler(Path(data_dir), force)
        return

    from nutrimaster.rag.jina import JinaRetriever

    fallback_retriever = JinaRetriever()
    fallback_retriever.build_index(data_dir=data_dir, incremental=True, force=force)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  _TeeWriter — 同时写入 stdout 和内存缓冲区                                 ║
# ║  用于捕获 process_one_paper 的 print 输出，不影响终端显示                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝

class _TeeWriter:
    """将写入内容同时输出到原始流和内存缓冲区（线程安全）。"""

    def __init__(self, original, max_chars=200_000):
        self._original = original    # 原始 stdout/stderr
        self._buf = io.StringIO()    # 内存缓冲区
        self._max = max_chars        # 缓冲区最大字符数（防止内存爆炸）
        self._lock = threading.Lock()

    def write(self, s):
        """写入内容到原始流和缓冲区。"""
        self._original.write(s)
        with self._lock:
            self._buf.write(s)
            # 超过上限时截取尾部
            if self._buf.tell() > self._max:
                text = self._buf.getvalue()[-self._max:]
                self._buf = io.StringIO()
                self._buf.write(text)
        return len(s)

    def flush(self):
        self._original.flush()

    def get_tail(self, n=5000):
        """获取缓冲区最后 n 个字符（供 /api/pipeline/output 接口返回）。"""
        with self._lock:
            text = self._buf.getvalue()
            return text[-n:] if len(text) > n else text


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  认证装饰器                                                               ║
# ║  login_required: 验证 Supabase Bearer Token                              ║
# ║  admin_required: 额外检查邮箱 == ADMIN_EMAIL                              ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def _extract_token() -> str:
    """从 Authorization header 或 URL query param 提取 token。

    SSE 端点 (EventSource) 不支持自定义 header，所以通过 ?token=xxx 传递。
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return request.args.get("token", "")


def login_required(f):
    """验证 Supabase access token，成功后将 user 对象挂到 request.user。"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({"error": "未登录"}), 401
        if not supabase:
            return jsonify({"error": "Supabase 未配置"}), 500
        try:
            resp = supabase.auth.get_user(token)
            request.user = resp.user
        except Exception:
            return jsonify({"error": "认证失败，请重新登录"}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """在 login_required 基础上，额外检查 email 在 ADMIN_EMAILS 白名单中。"""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not ADMIN_EMAILS:
            return jsonify({"error": "ADMIN_EMAIL 未配置"}), 500
        if request.user.email not in ADMIN_EMAILS:
            return jsonify({"error": "仅管理员可访问"}), 403
        return f(*args, **kwargs)
    return decorated


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  辅助函数                                                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def get_processed_stems() -> set:
    """扫描 data/ 获取已处理文件的 stem 集合（用于上传去重）。

    例如文件 MinerU_markdown_PMC123_nutri_plant_verified.json
    → stem = "MinerU_markdown_PMC123"
    """
    return {
        f.name.replace("_nutri_plant_verified.json", "")
        for f in DATA_DIR.glob("*_nutri_plant_verified.json")
    }


def get_input_files() -> list:
    """获取 src/nutrimaster/extraction/input/ 中所有待处理的 .md 文件名（排序后）。"""
    if not INPUT_DIR.exists():
        return []
    return sorted(f for f in os.listdir(INPUT_DIR) if f.endswith(".md"))


def _sse_event(event: str, data: dict) -> str:
    """格式化一条 SSE 事件字符串。"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _apply_settings(settings: dict):
    """将前端传入的参数应用到 extractor 模块的运行时变量。

    因为 extractor 的 config 是模块级导入（import 时复制值），
    所以需要直接修改目标模块的变量才能生效。
    """
    import nutrimaster.extraction.extract as _ext
    import nutrimaster.extraction.verify as _ver

    # 提取温度（extract.py 第 185 行用 TEMPERATURE 变量）
    if "temperature" in settings:
        val = max(PIPELINE_LIMITS["temperature"][0],
                  min(PIPELINE_LIMITS["temperature"][1], float(settings["temperature"])))
        _ext.TEMPERATURE = val

    # 验证批次基因数（verify.py 的 GENES_PER_BATCH 模块变量）
    if "verify_batch_genes" in settings:
        val = max(PIPELINE_LIMITS["verify_batch_genes"][0],
                  min(PIPELINE_LIMITS["verify_batch_genes"][1], int(settings["verify_batch_genes"])))
        _ver.GENES_PER_BATCH = val



# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  路由：静态文件 & 配置                                                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@admin_bp.route("/")
def index():
    """返回 Admin SPA 首页。"""
    return send_from_directory(str(Path(__file__).parent / "static"), "index.html")


@admin_bp.route("/api/config")
def api_config():
    """返回前端需要的 Supabase 公钥配置（无需认证）。"""
    return jsonify({
        "supabase_url": SUPABASE_URL,
        "supabase_anon_key": SUPABASE_ANON_KEY,
    })


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  路由：Dashboard 状态                                                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@admin_bp.route("/api/status")
@admin_required
def api_status():
    """返回 Dashboard 统计数据 + pipeline 运行状态。"""
    input_count = len(get_input_files())
    processed_count = len(list(DATA_DIR.glob("*_nutri_plant_verified.json")))
    # "Archive" = 已处理过的 .md（被移入 processed 目录）
    waitlist_dir = REPO_ROOT / "extractor" / "input" / "processed"
    waitlist_count = len(list(waitlist_dir.glob("*.md"))) if waitlist_dir.exists() else 0

    with _lock:
        running = pipeline_state["running"]
        done = pipeline_state["done"]
        total = pipeline_state["total"]

    return jsonify({
        "input_queue": input_count,
        "processed_total": processed_count,
        "waitlist": waitlist_count,
        "pipeline_running": running,
        "pipeline_done": done,
        "pipeline_total": total,
    })


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  路由：ZIP 上传                                                           ║
# ║  递归解压所有嵌套 zip → 提取 .md → 去重后存入 src/nutrimaster/extraction/input/               ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@admin_bp.route("/api/upload", methods=["POST"])
@admin_required
def api_upload():
    """上传 zip 文件，递归解压并将 .md 文件放入 input 目录。

    去重规则：
      1. stem 已在 data/ 中有 verified JSON → 跳过（"已在库中"）
      2. stem 已在 src/nutrimaster/extraction/input/ 中 → 跳过（"已在队列中"）
    """
    if "file" not in request.files:
        return jsonify({"error": "未选择文件"}), 400

    f = request.files["file"]
    if not f.filename or not f.filename.endswith(".zip"):
        return jsonify({"error": "请上传 .zip 文件"}), 400

    ensure_dirs()
    processed_stems = get_processed_stems()
    existing_input = {Path(n).stem for n in get_input_files()}

    new_files = []          # 新增到 input 的文件
    skipped_processed = []  # 跳过：data 中已有
    skipped_existing = []   # 跳过：input 中已有

    def extract_recursive(buf: BytesIO):
        """递归解压：zip 里的 zip 继续解压，直到提取出所有 .md 文件。"""
        try:
            with zipfile.ZipFile(buf) as zf:
                for name in zf.namelist():
                    # 跳过 macOS 元数据和目录条目
                    if name.startswith("__MACOSX") or name.endswith("/"):
                        continue
                    entry_data = zf.read(name)
                    if name.endswith(".zip"):
                        # 嵌套 zip → 递归
                        extract_recursive(BytesIO(entry_data))
                    elif name.endswith(".md"):
                        basename = Path(name).name
                        stem = Path(basename).stem
                        if stem in processed_stems:
                            skipped_processed.append(basename)
                        elif stem in existing_input:
                            skipped_existing.append(basename)
                        else:
                            dest = Path(INPUT_DIR) / basename
                            dest.write_bytes(entry_data)
                            new_files.append(basename)
                            existing_input.add(stem)
        except zipfile.BadZipFile:
            pass  # 非 zip 文件，静默跳过

    try:
        extract_recursive(BytesIO(f.read()))
    except Exception as e:
        return jsonify({"error": f"解压失败: {e}"}), 400

    if not new_files and not skipped_processed and not skipped_existing:
        return jsonify({"error": "未在 zip 中找到任何 .md 文件（已递归搜索嵌套 zip）"}), 400

    return jsonify({
        "new_files": new_files,
        "skipped_processed": skipped_processed,
        "skipped_existing": skipped_existing,
    })


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  路由：Pipeline 预览 / 运行 / SSE 流 / 停止 / 输出                        ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@admin_bp.route("/api/pipeline/settings")
@admin_required
def api_pipeline_settings():
    """返回当前可调参数的值和允许范围，供前端 Settings 面板初始化。"""
    import nutrimaster.extraction.extract as _ext
    import nutrimaster.extraction.verify as _ver

    return jsonify({
        "values": {
            "temperature": getattr(_ext, "TEMPERATURE", PIPELINE_DEFAULTS["temperature"]),
            "verify_batch_genes": getattr(_ver, "GENES_PER_BATCH", PIPELINE_DEFAULTS["verify_batch_genes"]),
            "max_workers": PIPELINE_DEFAULTS["max_workers"],
        },
        "limits": PIPELINE_LIMITS,
    })


@admin_bp.route("/api/pipeline/preview", methods=["POST"])
@admin_required
def api_pipeline_preview():
    """同步处理 input 中第一篇论文，返回 verified JSON 供用户确认格式。

    预览是真实处理——.md 会移入 processed，JSON 写入 data/。
    前端可传入 settings 字段覆盖 temperature 等参数。
    预览不是强制步骤，用户也可以直接点 "Run All"。
    """
    files = get_input_files()
    if not files:
        return jsonify({"error": "input 目录中没有待处理文件"}), 400

    with _lock:
        if pipeline_state["running"]:
            return jsonify({"error": "Pipeline 正在运行中"}), 409

    # 读取并应用前端传入的参数
    body = request.get_json(silent=True) or {}
    if "settings" in body:
        _apply_settings(body["settings"])

    filename = files[0]
    md_path = Path(INPUT_DIR) / filename
    stem = Path(filename).stem
    tracker = TokenTracker(model=os.getenv("MODEL", "unknown"))

    ensure_dirs()

    # 捕获 process_one_paper 的 print 输出
    import sys
    tee = _TeeWriter(sys.__stdout__)
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = tee
    try:
        result = process_one_paper(md_path, stem, tracker)
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    pipeline_state["output"] = tee.get_tail(5000)
    token_report = save_token_report(tracker, "admin-preview")

    # 读取生成的 verified JSON（如果处理成功）
    verified_path = DATA_DIR / f"{stem}_nutri_plant_verified.json"
    verified_data = None
    if verified_path.exists():
        try:
            verified_data = json.loads(verified_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    return jsonify({
        "filename": filename,
        "status": result.get("status", "failed"),
        "verified_json": verified_data,
        "token_summary": tracker.get_summary(),
        "token_report": token_report,
    })


@admin_bp.route("/api/pipeline/run", methods=["POST"])
@admin_required
def api_pipeline_run():
    """后台线程并行处理 input 中所有 .md 文件。

    实际批处理循环复用 extractor.pipeline.run_pipeline_batch()。
    admin 只负责参数、SSE、停止信号和索引重建。
    前端可传入 settings 覆盖参数（temperature、verify_batch_genes、max_workers）。
    处理进度通过 SSE (/api/pipeline/stream) 实时推送。
    全部完成后自动重建 RAG 向量索引。
    """
    with _lock:
        if pipeline_state["running"]:
            return jsonify({"error": "Pipeline 正在运行中"}), 409

    files = get_input_files()
    if not files:
        return jsonify({"error": "没有待处理文件"}), 400

    # 读取前端传入的参数
    body = request.get_json(silent=True) or {}
    settings = body.get("settings", {})
    max_workers = int(settings.get("max_workers", PIPELINE_DEFAULTS["max_workers"]))
    max_workers = max(PIPELINE_LIMITS["max_workers"][0],
                      min(PIPELINE_LIMITS["max_workers"][1], max_workers))

    # 应用 temperature 和 verify_batch_genes
    if settings:
        _apply_settings(settings)

    # 初始化 pipeline 状态
    with _lock:
        pipeline_state["running"] = True
        pipeline_state["stop_requested"] = False
        pipeline_state["done"] = 0
        pipeline_state["current_file"] = ""
        # 清空旧事件
        while not pipeline_state["events"].empty():
            try:
                pipeline_state["events"].get_nowait()
            except queue.Empty:
                break

    # ── 过滤掉 data 中已有 verified JSON 的文件（只看 data 目录，不管 report）──
    processed_stems = get_processed_stems()
    todo_files = [f for f in files if Path(f).stem not in processed_stems]
    skipped = len(files) - len(todo_files)

    if not todo_files:
        with _lock:
            pipeline_state["running"] = False
        return jsonify({"error": f"全部 {len(files)} 篇已在 data 中，无需处理"}), 400

    with _lock:
        pipeline_state["total"] = len(todo_files)

    def run():
        """后台线程：并行处理所有论文 → 重建索引。"""
        import sys
        tee = _TeeWriter(sys.__stdout__)
        pipeline_state["_tee"] = tee
        sys.stdout = sys.stderr = tee

        stopped = False
        tracker = None

        try:
            eq = pipeline_state["events"]
            tracker = TokenTracker(model=os.getenv("MODEL", "unknown"))
            pipeline_state["tracker"] = tracker
            ensure_dirs()

            if skipped > 0:
                print(f"  ⏭️  跳过 {skipped} 篇（data 中已有 verified JSON）")

            eq.put(("start", {"total": len(todo_files), "workers": max_workers, "skipped": skipped}))

            if max_workers > 1 and len(todo_files) > 1:
                # 并行模式下不追踪单一 current_file，前端只显示整体并行状态。
                eq.put(("processing", {
                    "index": 0,
                    "filename": f"{len(todo_files)} papers (parallel, {max_workers} workers)",
                    "total": len(todo_files),
                }))

            def _stop_requested() -> bool:
                with _lock:
                    return pipeline_state["stop_requested"]

            def _on_paper_start(filename: str, index: int, total: int, parallel: bool):
                # 顺序模式下逐篇广播当前文件；并行模式已在上面发送总体状态。
                if parallel:
                    return
                with _lock:
                    pipeline_state["current_file"] = filename
                eq.put(("processing", {"index": index, "filename": filename, "total": total}))

            def _on_paper_done(filename: str, result: dict, done: int, total: int, parallel: bool):
                status = result.get("status", "failed")
                with _lock:
                    pipeline_state["done"] = done
                eq.put(("paper_done", {
                    "index": done - 1,
                    "filename": filename,
                    "status": status,
                    "done": done,
                    "total": total,
                }))

            run_result = run_pipeline_batch(
                todo_files,
                input_dir=Path(INPUT_DIR),
                workers=max_workers,
                tracker=tracker,
                stop_requested=_stop_requested,
                on_paper_start=_on_paper_start,
                on_paper_done=_on_paper_done,
            )
            stopped = run_result["stopped"]
            # ── 全部完成：重建 RAG 索引 ──────────────────────────
            if not stopped:
                eq.put(("rebuilding_index", {}))
                try:
                    _refresh_index(DATA_DIR, force=False)
                    eq.put(("index_rebuilt", {}))
                except Exception as e:
                    eq.put(("index_error", {"error": str(e)}))

                token_summary = tracker.get_summary()
                token_report = save_token_report(tracker, "admin-run")
                eq.put(("complete", {
                    "done": len(todo_files),
                    "total": len(todo_files),
                    "token_summary": token_summary,
                    "token_report": token_report,
                }))

            elif tracker:
                token_summary = tracker.get_summary()
                token_report = save_token_report(tracker, "admin-run")
                eq.put(("stopped", {
                    "done": pipeline_state["done"],
                    "total": len(todo_files),
                    "token_summary": token_summary,
                    "token_report": token_report,
                }))

        finally:
            sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
            pipeline_state["output"] = tee.get_tail(5000)
            pipeline_state["_tee"] = None
            pipeline_state["tracker"] = None

            with _lock:
                pipeline_state["running"] = False
                pipeline_state["current_file"] = ""

    t = threading.Thread(target=run, daemon=True)
    pipeline_state["thread"] = t
    t.start()

    msg = f"Pipeline 已启动，共 {len(todo_files)} 篇论文，{max_workers} 并行"
    if skipped > 0:
        msg += f"（跳过 {skipped} 篇已处理）"

    return jsonify({
        "message": msg,
        "total": len(todo_files),
        "skipped": skipped,
        "workers": max_workers,
    })


@admin_bp.route("/api/pipeline/stream")
@admin_required
def api_pipeline_stream():
    """SSE 端点：流式推送 pipeline 处理进度事件。

    事件类型：
      connected       — 连接成功
      start           — pipeline 开始
      processing      — 开始处理某篇论文
      paper_done      — 某篇论文处理完成
      rebuilding_index — 正在重建 RAG 索引
      index_rebuilt   — 索引重建成功
      index_error     — 索引重建失败
      complete        — 全部完成
      stopped         — 被用户停止
      heartbeat       — 30秒无事件时的心跳
      idle            — pipeline 已不在运行（兜底）
    """
    def generate():
        eq = pipeline_state["events"]
        yield _sse_event("connected", {"message": "SSE connected"})
        while True:
            try:
                event_type, data = eq.get(timeout=30)
                yield _sse_event(event_type, data)
                if event_type in ("complete", "stopped"):
                    break
            except queue.Empty:
                # 30秒没有新事件 → 发心跳保活
                yield _sse_event("heartbeat", {})
                with _lock:
                    if not pipeline_state["running"]:
                        yield _sse_event("idle", {})
                        break

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@admin_bp.route("/api/pipeline/stop", methods=["POST"])
@admin_required
def api_pipeline_stop():
    """发送停止信号。当前正在处理的论文会完成后停止，不清理半成品。"""
    with _lock:
        if not pipeline_state["running"]:
            return jsonify({"error": "Pipeline 未在运行"}), 400
        pipeline_state["stop_requested"] = True

    return jsonify({"message": "停止信号已发送，当前论文处理完成后停止"})


@admin_bp.route("/api/pipeline/output")
@admin_required
def api_pipeline_output():
    """返回 pipeline 的 console 输出（最后 5000 字符）。

    运行中：从 _TeeWriter 实时读取。
    运行结束：从缓存的 output 字符串读取。
    """
    tee = pipeline_state.get("_tee")
    if tee:
        return jsonify({"output": tee.get_tail(5000)})
    return jsonify({"output": pipeline_state.get("output", "")})


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  路由：已处理论文列表                                                      ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@admin_bp.route("/api/papers")
@admin_required
def api_papers():
    """扫描语料目录返回所有已处理论文的列表（文件名、标题、修改时间）。"""
    papers = []
    for f in sorted(DATA_DIR.glob("*_nutri_plant_verified.json")):
        if f.name == ".gitkeep":
            continue
        title = ""
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            title = data.get("Title", "")
        except Exception:
            pass
        papers.append({
            "filename": f.name,
            "title": title,
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(timespec="seconds"),
        })
    papers.sort(key=lambda p: p["modified"], reverse=True)
    return jsonify(papers)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  路由：Prompt / Schema 编辑器                                             ║
# ║  保存后自动清除 lru_cache，下次 pipeline 使用新版本                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@admin_bp.route("/api/prompt", methods=["GET"])
@admin_required
def api_prompt_get():
    """读取当前 prompt 文件内容。"""
    if not PROMPT_PATH.exists():
        return jsonify({"error": "Prompt 文件不存在"}), 404
    return jsonify({"content": PROMPT_PATH.read_text(encoding="utf-8"), "path": str(PROMPT_PATH)})


@admin_bp.route("/api/prompt", methods=["PUT"])
@admin_required
def api_prompt_put():
    """保存 prompt 文件，并清除 extractor 的 lru_cache 使新内容生效。"""
    body = request.get_json(silent=True)
    if not body or "content" not in body:
        return jsonify({"error": "缺少 content 字段"}), 400
    PROMPT_PATH.write_text(body["content"], encoding="utf-8")
    # 清除 lru_cache → 下次 extract 会重新读取文件
    try:
        from nutrimaster.extraction.extract import _load_prompt
        _load_prompt.cache_clear()
    except Exception:
        pass
    return jsonify({"message": "Prompt 已保存", "length": len(body["content"])})


@admin_bp.route("/api/schema", methods=["GET"])
@admin_required
def api_schema_get():
    """读取当前 schema 文件内容。"""
    if not SCHEMA_PATH.exists():
        return jsonify({"error": "Schema 文件不存在"}), 404
    return jsonify({"content": SCHEMA_PATH.read_text(encoding="utf-8"), "path": str(SCHEMA_PATH)})


@admin_bp.route("/api/schema", methods=["PUT"])
@admin_required
def api_schema_put():
    """保存 schema 文件（先验证 JSON 合法性），并清除 lru_cache。"""
    body = request.get_json(silent=True)
    if not body or "content" not in body:
        return jsonify({"error": "缺少 content 字段"}), 400
    # 验证 JSON 格式
    try:
        json.loads(body["content"])
    except json.JSONDecodeError as e:
        return jsonify({"error": f"无效的 JSON: {e}"}), 400
    SCHEMA_PATH.write_text(body["content"], encoding="utf-8")
    try:
        from nutrimaster.extraction.extract import _load_extract_all_schema
        _load_extract_all_schema.cache_clear()
    except Exception:
        pass
    return jsonify({"message": "Schema 已保存", "length": len(body["content"])})


@admin_bp.route("/api/pipeline/tokens")
@admin_required
def api_pipeline_tokens():
    """实时返回当前 pipeline 运行的 token 用量。"""
    tracker = pipeline_state.get("tracker")
    if tracker is None:
        return jsonify({"summary": None})
    return jsonify({"summary": tracker.get_summary()})
