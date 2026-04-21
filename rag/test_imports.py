#!/usr/bin/env python3
"""
测试 rag 模块的导入是否正常
用法: python test_imports.py
"""
import sys
from pathlib import Path

# 模拟 app.py 的路径设置
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试所有关键模块的导入"""
    print("=" * 60)
    print("测试 RAG 模块导入")
    print("=" * 60)

    tests = [
        ("core.config", "配置模块"),
        ("core.llm_client", "LLM 客户端"),
        ("core.agent", "Agent 核心"),
        ("utils.data_loader", "数据加载器"),
        ("search.retriever", "向量检索器"),
        ("search.reranker", "Reranker"),
        ("search.personal_lib", "个人知识库"),
        ("tools.pubmed_search", "PubMed 搜索工具"),
        ("tools.gene_db_search", "基因库搜索工具"),
        ("tools.rag_search", "RAG 搜索工具"),
    ]

    passed = 0
    failed = 0

    for module_name, description in tests:
        try:
            __import__(module_name)
            print(f"✓ {description:20s} ({module_name})")
            passed += 1
        except Exception as e:
            print(f"✗ {description:20s} ({module_name})")
            print(f"  错误: {e}")
            failed += 1

    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
