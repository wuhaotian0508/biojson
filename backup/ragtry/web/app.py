#!/usr/bin/env python3
"""Flask Web 界面 - 基因信息 RAG 问答系统"""
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
import sys
from pathlib import Path

# 导入父目录的 RAG 组件（web/ → rag/）
sys.path.insert(0, str(Path(__file__).parent.parent))
from backup.ragtry.retriever import JinaRetriever
from backup.ragtry.generator import RAGGenerator

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# 全局初始化 RAG 系统
print("初始化 RAG 系统...")
retriever = JinaRetriever()
retriever.build_index(force=False)
generator = RAGGenerator()
print("初始化完成！")


@app.route('/')
def index():
    """返回前端页面"""
    return app.send_static_file('index.html')


@app.route('/api/health')
def health():
    """健康检查"""
    return jsonify({"status": "ok", "rag_ready": True})


@app.route('/api/query', methods=['POST'])
def query():
    """SSE 流式问答接口"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()

        if not question:
            return jsonify({"error": "问题不能为空"}), 400

        def generate():
            try:
                # 1. 检索相关基因
                results = retriever.retrieve(question, use_rerank=True)
                sources = [
                    {
                        "gene": chunk.gene_name,
                        "article": chunk.article_title[:50] + "..." if len(chunk.article_title) > 50 else chunk.article_title,
                        "score": float(score)
                    }
                    for chunk, score in results[:5]
                ]
                yield f"event: sources\ndata: {json.dumps(sources, ensure_ascii=False)}\n\n"

                # 2. 流式生成答案
                for token in generator.generate_stream(question, results):
                    yield f"event: token\ndata: {json.dumps({'content': token}, ensure_ascii=False)}\n\n"

                # 3. 完成
                yield f"event: done\ndata: {{}}\n\n"

            except Exception as e:
                import traceback
                traceback.print_exc()
                yield f"event: error\ndata: {json.dumps({'message': str(e)}, ensure_ascii=False)}\n\n"

        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
