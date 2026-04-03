
#!/usr/bin/env python3
"""
Flask web 应用 - 提供 RAG 问答 Web 界面
支持：基因库检索 / 联网搜索 / 个人知识库 / 深度调研
"""
import sys
import logging
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
# 添加项目根目录到路径（for admin blueprint）
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from flask import Flask, render_template, request, jsonify, Response
import json
import time
import numpy as np
# 使用Jina向量检索器（语义检索 + rerank）
from retriever import JinaRetriever as Retriever
from generator import RAGGenerator as Generator
from online_search import OnlineSearcher
from personal_lib import PersonalLibrary
import config
# ---- 技能系统（从 skills/ 目录加载） ----
from skills.skill_loader import SkillLoader
from skills.crispr_experiment.pipeline import ExperimentPipeline
from config import (
    DEEP_TOP_K_RETRIEVAL, DEEP_TOP_K_RERANK,
    TOP_K_RERANK, JINA_RERANK_URL, RERANK_MODEL, JINA_API_KEY,
)
# ===== 登录功能 =====
from web.auth import login_required, user_profile_view, update_profile_view, delete_account_view
from admin.app import admin_bp
import requests as http_requests
import tempfile

logger = logging.getLogger(__name__)

app = Flask(__name__)

# 注册 admin 管理后台到 /admin 路径
app.register_blueprint(admin_bp, url_prefix="/admin")

# 全局初始化
print("初始化检索器...")
retriever = Retriever()
retriever.build_index()

print("初始化联网搜索...")
online_searcher = OnlineSearcher()

print("初始化生成器...")
generator = Generator()
skill_loader = SkillLoader()

# 个人库实例缓存 {user_id: PersonalLibrary}
_personal_libs: dict = {}

print("系统就绪！")


def _get_personal_lib(user) -> PersonalLibrary:
    """获取当前用户的个人库实例（懒加载）"""
    uid = user.id
    if uid not in _personal_libs:
        _personal_libs[uid] = PersonalLibrary(uid)
    return _personal_libs[uid]


def _gene_chunks_to_dicts(chunks) -> list:
    """将 (GeneChunk, score) 列表转为统一 dict 格式"""
    results = []
    for chunk, score in chunks:
        results.append({
            "source_type": "gene_db",
            "title": chunk.paper_title,
            "content": chunk.content,
            "url": chunk.doi or "",
            "score": float(score),
            "metadata": {
                "gene_name": chunk.gene_name,
                "journal": chunk.journal,
                "gene_type": chunk.gene_type,
                "doi": chunk.doi,
            },
        })
    return results


def _jina_rerank(query: str, candidates: list, top_n: int,
                 max_retries: int = 3) -> list:
    """使用 Jina Reranker 对统一 dict 列表重排序（带重试）"""
    if not candidates:
        return []
    documents = [c["content"] for c in candidates]
    headers = {
        "Authorization": f"Bearer {JINA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": RERANK_MODEL,
        "query": query,
        "documents": documents,
        "top_n": min(top_n, len(candidates)),
    }
    for attempt in range(1, max_retries + 1):
        try:
            resp = http_requests.post(JINA_RERANK_URL, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
            reranked = []
            for item in resp.json()["results"]:
                idx = item["index"]
                entry = dict(candidates[idx])
                entry["score"] = item["relevance_score"]
                reranked.append(entry)
            return reranked
        except Exception as e:
            logger.warning("Jina rerank attempt %d/%d failed: %s", attempt, max_retries, e)
            if attempt < max_retries:
                time.sleep(1 * attempt)
    logger.warning("Jina rerank exhausted all retries, returning original order")
    return candidates[:top_n]


def _sse(payload: dict) -> str:
    """序列化 SSE 事件。"""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _resolve_experiment_genes(pipeline: ExperimentPipeline, args: dict) -> list[dict]:
    """
    解析待编辑基因列表，支持三种来源（按优先级）：

    1. 显式基因列表（genes）: 前端传入完整的 [{"gene": ..., "species": ...}]
    2. 用户选定的基因名（genes_selected）: 前端基因编辑器传入的纯基因名列表，
       需要调用 LLM 从回答上下文中解析物种信息
    3. 自动提取（fallback）: 从 answer_text 或 query 中由 LLM 自动提取

    参数:
        pipeline: ExperimentPipeline 实例
        args: 包含 genes / genes_selected / answer_text / query 的参数字典

    返回:
        [{"gene": "GmFAD2", "species": "Glycine max"}, ...]
    """
    # ---- 路径 1: 完整基因列表（含物种），直接使用 ----
    genes = args.get("genes")
    if genes:
        return genes

    # ---- 路径 2: 用户选定的基因名列表（仅名称，需 LLM 解析物种） ----
    genes_selected = args.get("genes_selected")
    if genes_selected:
        source_text = (args.get("answer_text") or args.get("query") or "").strip()
        return pipeline.extract_selected_genes_with_llm(source_text, genes_selected)

    # ---- 路径 3: 从查询+回答文本中自动提取 ----
    # 合并 query 和 answer_text：query 中有用户指定的基因名，
    # answer_text 中有 LLM 补充的物种/上下文信息，两者都需要
    query_text = (args.get("query") or "").strip()
    answer_text = (args.get("answer_text") or "").strip()
    source_text = f"{query_text}\n{answer_text}".strip()
    if not source_text:
        raise ValueError("缺少可用于提取基因的 query 或 answer_text")

    return pipeline.extract_genes_with_llm(source_text)


def _stream_experiment_events(tool_call: dict):
    """执行技能对应的实验 pipeline，并产出统一事件。"""
    skill_name = tool_call.get("skill", "crispr-experiment")
    skill_loader.get_skill(skill_name)
    args = tool_call.get("args", {})

    pipeline = ExperimentPipeline()
    try:
        genes = _resolve_experiment_genes(pipeline, args)
        yield {
            "type": "experiment_start",
            "genes": [g["gene"] for g in genes],
        }
        for event in pipeline.run_all_from_genes(genes):
            yield event
    finally:
        pipeline.cleanup()


# ------------------------------------------------------------------
# 页面路由
# ------------------------------------------------------------------

@app.route('/')
def index():
    """首页"""
    return app.send_static_file('index.html')


# ------------------------------------------------------------------
# 统一查询接口
# ------------------------------------------------------------------

@app.route('/api/query', methods=['POST'])
@login_required
def query():
    """处理查询请求 - SSE 流式输出

    请求体: { query, use_personal: bool, use_depth: bool }
    """
    data = request.get_json() or {}
    query_text = data.get('query', '').strip()
    use_personal = data.get('use_personal', False)
    use_depth = data.get('use_depth', False)

    if not query_text:
        return jsonify({'error': '查询不能为空'}), 400

    def generate():
        try:
            # ---- 快速路径：用户明确要求 SOP 时，跳过检索/生成，直接执行 pipeline ----
            if skill_loader.should_trigger(query=query_text, trigger_source="query"):
                tool_call = skill_loader.build_tool_call(
                    query=query_text, answer_text="", trigger_source="query",
                )
                if tool_call:
                    try:
                        for event in _stream_experiment_events(tool_call):
                            yield _sse(event)
                        yield _sse({'type': 'done'})
                        return
                    except Exception:
                        logger.info("SOP 快速路径未提取到基因，回退到常规流程")

            all_candidates = []

            # 1) 联网搜索 — 始终执行
            yield _sse({'type': 'searching', 'data': '正在搜索 PubMed 文献...'})
            online_results = online_searcher.search_all(query_text)
            all_candidates.extend(online_results)

            # 2) 基因库检索 — 仅 use_depth 时
            if use_depth:
                yield _sse({'type': 'searching', 'data': '正在检索基因数据库（深度模式）...'})
                gene_candidates = retriever.search(query_text, top_k=DEEP_TOP_K_RETRIEVAL)
                gene_dicts = _gene_chunks_to_dicts(gene_candidates)
                all_candidates.extend(gene_dicts)

            # 3) 个人库检索 — 仅 use_personal 时
            if use_personal:
                yield _sse({'type': 'searching', 'data': '正在检索个人知识库...'})
                try:
                    lib = _get_personal_lib(request.user)
                    q_emb = retriever.get_query_embedding(query_text)
                    personal_results = lib.search(q_emb, top_k=10)
                    all_candidates.extend(personal_results)
                except Exception as e:
                    logger.warning("Personal lib search failed: %s", e)

            # 4) 统一 rerank
            if all_candidates:
                yield _sse({'type': 'searching', 'data': '正在对结果进行排序...'})
                top_n = DEEP_TOP_K_RERANK if use_depth else TOP_K_RERANK
                ranked = _jina_rerank(query_text, all_candidates, top_n)
            else:
                ranked = []

            # 5) 发送来源
            sources = []
            for item in ranked:
                src = {
                    "source_type": item["source_type"],
                    "title": item.get("title", ""),
                    "score": item.get("score", 0.0),
                    "url": item.get("url", ""),
                }
                meta = item.get("metadata", {})
                src["paper_title"] = item.get("title", "")
                src["gene_name"] = meta.get("gene_name", "")
                src["journal"] = meta.get("journal", "")
                src["doi"] = meta.get("doi", "")
                src["pmid"] = meta.get("pmid", "")
                src["filename"] = meta.get("filename", "")
                src["page"] = meta.get("page", "")
                sources.append(src)

            yield _sse({'type': 'sources', 'data': sources})

            # 6) LLM 生成
            answer_text = ""
            for event in generator.generate_stream_with_tools(query_text, ranked, use_depth=use_depth):
                if event["type"] == "text":
                    answer_text += event["data"]
                    yield _sse({'type': 'text', 'data': event['data']})

            # 7) 检测是否应自动触发 SOP 生成或显示基因编辑器
            #    auto-trigger: 用户输入同时包含 sop + 基因编辑操作 + 具体基因名
            #    → 直接执行 pipeline，无需用户点击按钮
            auto_trigger = skill_loader.should_trigger(
                query=query_text, answer_text=answer_text, trigger_source="query"
            )

            if auto_trigger and answer_text:
                # ---- 自动触发 SOP pipeline ----
                # 用户输入明确要求 SOP（如"请帮我设计 GmFAD2 的 CRISPR 敲除 SOP"）
                # 直接在同一 SSE 流中执行实验方案生成
                tool_call = skill_loader.build_tool_call(
                    query=query_text,
                    answer_text=answer_text,
                    trigger_source="query",
                )
                if tool_call:
                    for event in _stream_experiment_events(tool_call):
                        yield _sse(event)

            elif answer_text:
                # ---- 非自动触发：检测回答中的基因名，发送给前端 ----
                # 前端收到基因列表后显示可编辑的基因芯片 + SOP 按钮
                detected_genes = skill_loader.extract_gene_names(answer_text)
                if detected_genes:
                    yield _sse({
                        'type': 'genes_available',
                        'genes': detected_genes,  # 基因名列表，如 ["GmFAD2", "AtMYB4"]
                    })

            yield _sse({'type': 'done'})

        except Exception as e:
            logger.exception("Query error")
            yield _sse({'type': 'error', 'data': str(e)})

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/experiment/run', methods=['POST'])
@login_required
def run_experiment():
    """
    显式触发实验方案生成（由前端 SOP 按钮触发）。

    请求体支持的参数：
    - genes_selected: 用户在基因编辑器中选定的基因名列表（推荐方式）
                      如 ["GmFAD2", "AtMYB4"]
    - genes:          完整基因列表 [{"gene": ..., "species": ...}]
    - answer_text:    LLM 回答文本（用于 LLM 提取基因/物种）
    - query:          用户原始查询
    - skill:          技能名称（默认 "crispr-experiment"）
    """
    data = request.get_json() or {}
    genes = data.get('genes')
    genes_selected = data.get('genes_selected')  # 前端基因编辑器传入的纯基因名列表
    answer_text = data.get('answer_text', '').strip()
    query_text = data.get('query', '').strip()
    skill_name = data.get('skill', 'crispr-experiment').strip() or 'crispr-experiment'

    if not genes and not genes_selected and not answer_text and not query_text:
        return jsonify({'error': '缺少 genes、genes_selected、answer_text 或 query'}), 400

    try:
        tool_call = skill_loader.build_tool_call(
            query=query_text,
            answer_text=answer_text,
            genes=genes,
            trigger_source='button',
            skill_name=skill_name,
        )
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    if not tool_call:
        return jsonify({'error': '未匹配到可执行技能'}), 400

    # ---- 将 genes_selected 传入 tool_call args，供 _resolve_experiment_genes 使用 ----
    if genes_selected:
        tool_call["args"]["genes_selected"] = genes_selected

    def generate():
        try:
            for event in _stream_experiment_events(tool_call):
                yield _sse(event)
            yield _sse({'type': 'done'})
        except Exception as e:
            logger.exception("Experiment API error")
            yield _sse({'type': 'error', 'data': str(e)})

    return Response(generate(), mimetype='text/event-stream')


# ------------------------------------------------------------------
# 个人知识库接口
# ------------------------------------------------------------------

@app.route('/api/personal/upload', methods=['POST'])
@login_required
def personal_upload():
    """上传 PDF 到个人库"""
    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400

    f = request.files['file']
    if not f.filename or not f.filename.lower().endswith('.pdf'):
        return jsonify({'error': '仅支持 PDF 文件'}), 400

    try:
        lib = _get_personal_lib(request.user)
        info = lib.upload_pdf(f, f.filename)
        return jsonify({'status': 'ok', 'file': info})
    except (ValueError, ImportError) as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.exception("Upload failed")
        return jsonify({'error': f'上传失败: {e}'}), 500


@app.route('/api/personal/files', methods=['GET'])
@login_required
def personal_files():
    """列出个人库文件"""
    lib = _get_personal_lib(request.user)
    return jsonify({'files': lib.list_files()})


@app.route('/api/personal/files/<filename>', methods=['DELETE'])
@login_required
def personal_delete(filename):
    """删除个人库文件"""
    lib = _get_personal_lib(request.user)
    if lib.delete_file(filename):
        return jsonify({'status': 'ok'})
    return jsonify({'error': '文件不存在'}), 404


@app.route('/api/personal/files/<filename>/rename', methods=['PUT'])
@login_required
def personal_rename(filename):
    """重命名个人库文件"""
    data = request.get_json()
    new_name = data.get('new_name', '').strip()
    if not new_name:
        return jsonify({'error': '新文件名不能为空'}), 400

    lib = _get_personal_lib(request.user)
    if lib.rename_file(filename, new_name):
        return jsonify({'status': 'ok'})
    return jsonify({'error': '文件不存在'}), 404


# ------------------------------------------------------------------
# 用户信息接口
# ------------------------------------------------------------------

@app.route('/api/user/profile', methods=['GET'])
@login_required
def user_profile():
    """返回当前用户信息（邮箱、昵称、是否管理员）"""
    return user_profile_view()


@app.route('/api/user/profile', methods=['PUT'])
@login_required
def user_profile_update():
    """更新用户昵称/头像"""
    return update_profile_view()


@app.route('/api/user/account', methods=['DELETE'])
@login_required
def user_account_delete():
    """删除当前用户账号"""
    return delete_account_view()


# ------------------------------------------------------------------
# 其他接口
# ------------------------------------------------------------------

@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'total_chunks': len(retriever.chunks)
    })


# ===== 前端配置接口（新增）—— 返回 Supabase 公开配置给前端 =====
@app.route('/api/config', methods=['GET'])
def frontend_config():
    """返回前端需要的 Supabase 公开配置（anon key，不含 service role key）"""
    return jsonify({
        'supabase_url': config.SUPABASE_URL,
        'supabase_anon_key': config.SUPABASE_ANON_KEY,
        'admin_port': config.ADMIN_PORT,
    })


if __name__ == '__main__':
    app.run(
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        debug=config.DEBUG
    )
