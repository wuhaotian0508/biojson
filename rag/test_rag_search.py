#!/usr/bin/env python3
"""
测试 RAG 综合搜索工具
用法: python test_rag_search.py
"""
import sys
import asyncio
from pathlib import Path

# 添加父目录到路径（模拟 app.py 的设置）
sys.path.insert(0, str(Path(__file__).parent))

from tools.rag_search import RAGSearchTool
from tools.pubmed_search import PubmedSearchTool
from search.retriever import JinaRetriever
from search.reranker import JinaReranker


async def test_rag_search():
    """测试 RAG 综合搜索"""
    print("=" * 60)
    print("初始化 RAG 搜索工具")
    print("=" * 60)

    # 初始化组件
    print("\n1. 初始化 PubMed 搜索工具...")
    pubmed_tool = PubmedSearchTool()

    print("2. 初始化基因库检索器...")
    retriever = JinaRetriever()
    retriever.build_index()  # 加载或构建索引

    print("3. 初始化 Jina Reranker...")
    reranker = JinaReranker()

    print("4. 创建 RAG 搜索工具...")
    rag_tool = RAGSearchTool(
        pubmed_tool=pubmed_tool,
        retriever=retriever,
        reranker=reranker,
        get_personal_lib=None,  # 不使用个人知识库
        get_query_embedding=retriever.get_query_embedding
    )

    # 测试查询
    print("\n" + "=" * 60)
    print("测试查询")
    print("=" * 60)

    test_cases = [
        {
            "query": "DREB transcription factor drought stress",
            "sources": ["gene_db"],
            "top_n": 3,
            "description": "仅搜索基因数据库"
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n[测试 {i}] {test['description']}")
        print(f"查询: {test['query']}")
        print(f"数据源: {test['sources']}")
        print(f"返回数量: {test['top_n']}")
        print("-" * 60)

        try:
            result = await rag_tool.execute(
                query=test['query'],
                sources=test['sources'],
                top_n=test['top_n']
            )
            print(result)
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_rag_search())
