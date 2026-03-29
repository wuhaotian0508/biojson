#!/usr/bin/env python3
"""
Flask Web 应用 - 提供 RAG 问答 Web 界面
"""
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, jsonify, Response
import json
# 使用简单检索器（TF-IDF）
from simple_retriever import SimpleRetriever as Retriever
from generator import Generator
import config

app = Flask(__name__)

# 全局初始化
print("初始化检索器...")
retriever = Retriever()
retriever.build_index()

print("初始化生成器...")
generator = Generator()

print("系统就绪！")


@app.route('/')
def index():
    """首页"""
    return app.send_static_file('index.html')


@app.route('/api/query', methods=['POST'])
def query():
    """处理查询请求 - SSE 流式输出"""
    data = request.get_json()
    query_text = data.get('query', '').strip()

    if not query_text:
        return jsonify({'error': '查询不能为空'}), 400

    def generate():
        try:
            # 检索
            chunks = retriever.retrieve(query_text)

            # 发送检索结果
            sources = [
                {
                    'paper_title': chunk.paper_title,
                    'gene_name': chunk.gene_name,
                    'journal': chunk.journal,
                    'doi': chunk.doi,
                    'score': float(score)
                }
                for chunk, score in chunks
            ]

            yield f"data: {json.dumps({'type': 'sources', 'data': sources})}\n\n"

            # 生成答案 (流式)
            for text in generator.generate(query_text, chunks, stream=True):
                yield f"data: {json.dumps({'type': 'text', 'data': text})}\n\n"

            # 发送完成信号
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'total_chunks': len(retriever.chunks)
    })


if __name__ == '__main__':
    app.run(
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        debug=config.DEBUG
    )
