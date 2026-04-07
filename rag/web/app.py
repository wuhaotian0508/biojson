
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

# 组件
from search.retriever import JinaRetriever as Retriever
from generation.generator import RAGGenerator as Generator
from search.online_search import OnlineSearcher
from search.personal_lib import PersonalLibrary
from search.reranker import JinaReranker
from pipeline import RAGPipeline, QueryOptions
from skills.skill_loader import SkillLoader
import config

# 登录 & 管理
from web.auth import login_required, user_profile_view, update_profile_view, delete_account_view
from admin.app import admin_bp

# ------------------------------------------------------------------
# 日志初始化（必须在所有 import 之后、app 创建之前）
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    force=True,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.register_blueprint(admin_bp, url_prefix="/admin")

# ------------------------------------------------------------------
# 全局初始化
# ------------------------------------------------------------------
logger.info("开始初始化系统组件...")

logger.info("初始化检索器...")
retriever = Retriever()
retriever.build_index()
logger.info(f"检索器初始化完成，已加载 {len(retriever.chunks)} 个文档块")

logger.info("初始化联网搜索...")
online_searcher = OnlineSearcher()

logger.info("初始化生成器...")
generator = Generator()
reranker = JinaReranker()
skill_loader = SkillLoader()

# 个人库实例缓存 {user_id: PersonalLibrary}
_personal_libs: dict = {}


def _get_personal_lib(user) -> PersonalLibrary:
    """获取当前用户的个人库实例（懒加载）"""
    uid = user.id
    if uid not in _personal_libs:
        _personal_libs[uid] = PersonalLibrary(uid)
    return _personal_libs[uid]


pipeline = RAGPipeline(
    retriever=retriever,
    online_searcher=online_searcher,
    reranker=reranker,
    generator=generator,
    skill_loader=skill_loader,
    get_personal_lib=_get_personal_lib,
)

logger.info("✅ 系统初始化完成，所有组件就绪！")


# ------------------------------------------------------------------
# 工具函数
# ------------------------------------------------------------------

def _sse(payload: dict) -> str:
    """序列化 SSE 事件。"""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


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
    """处理查询请求 - SSE 流式输出"""
    data = request.get_json() or {}
    query_text = data.get('query', '').strip()
    logger.info(f"[/api/query] 收到查询请求: {query_text[:100]}...")
    if not query_text:
        logger.warning("[/api/query] 查询为空")
        return jsonify({'error': '查询不能为空'}), 400

    opts = QueryOptions(
        use_personal=data.get('use_personal', False),
        use_depth=data.get('use_depth', False),
        history=data.get('history', []),
        user=request.user,
    )

    def generate():
        try:
            for event in pipeline.run(query_text, opts):
                yield _sse(event)
            logger.info(f"[/api/query] 查询完成: {query_text[:50]}...")
        except Exception as e:
            logger.exception(f"[/api/query] 查询异常: {query_text[:50]}...")
            yield _sse({'type': 'error', 'data': str(e)})

    return Response(generate(), mimetype='text/event-stream')


# ------------------------------------------------------------------
# 实验方案接口
# ------------------------------------------------------------------

@app.route('/api/experiment/run', methods=['POST'])
@login_required
def run_experiment():
    """显式触发实验方案生成（由前端 SOP 按钮触发）。"""
    data = request.get_json() or {}
    genes = data.get('genes')
    genes_selected = data.get('genes_selected')
    answer_text = data.get('answer_text', '').strip()
    query_text = data.get('query', '').strip()
    skill_name = data.get('skill', 'crispr-experiment').strip() or 'crispr-experiment'
    logger.info(f"[/api/experiment/run] 收到实验方案请求: skill={skill_name}, genes={genes}")

    if not genes and not genes_selected and not answer_text and not query_text:
        logger.warning("[/api/experiment/run] 缺少必要参数")
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

    if genes_selected:
        tool_call["args"]["genes_selected"] = genes_selected

    def generate():
        try:
            for event in pipeline.run_experiment(tool_call):
                yield _sse(event)
            yield _sse({'type': 'done'})
            logger.info(f"[/api/experiment/run] 实验方案生成完成: {skill_name}")
        except Exception as e:
            logger.exception(f"[/api/experiment/run] 实验方案生成异常: {skill_name}")
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
    """返回当前用户信息"""
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


@app.route('/api/config', methods=['GET'])
def frontend_config():
    """返回前端需要的 Supabase 公开配置"""
    return jsonify({
        'supabase_url': config.SUPABASE_URL,
        'supabase_anon_key': config.SUPABASE_ANON_KEY,
        'admin_port': config.ADMIN_PORT,
        'site_url': config.SITE_URL,
    })


if __name__ == '__main__':
    logger.info(f"启动 Flask 服务: {config.WEB_HOST}:{config.WEB_PORT}, debug={config.DEBUG}")
    app.run(
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        debug=config.DEBUG,
        use_reloader=config.DEBUG,
        exclude_patterns=["*.pyc", "*.tmp", "*.swp", "*.log", "*/__pycache__/*"],
    )
