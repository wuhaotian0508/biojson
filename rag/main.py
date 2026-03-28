#!/usr/bin/env python3
"""RAG系统主入口 - 基因信息检索与问答"""
import argparse
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from retriever import JinaRetriever
from generator import RAGGenerator

class GeneRAG:
    """基因信息RAG系统"""

    def __init__(self, build_index: bool = False):
        print("初始化RAG系统...")
        self.retriever = JinaRetriever()
        self.retriever.build_index(force=build_index)
        self.generator = RAGGenerator()
        print("初始化完成！")

    def query(self, question: str, use_rerank: bool = True,
              stream: bool = True, show_sources: bool = True) -> str:
        """执行RAG查询"""
        print(f"\n{'='*60}")
        print(f"问题: {question}")
        print('='*60)

        # 检索
        print("\n[1/2] 检索相关基因信息...")
        results = self.retriever.retrieve(question, use_rerank=use_rerank)

        if show_sources:
            print(f"\n检索到 {len(results)} 条相关记录:")
            for i, (chunk, score) in enumerate(results[:5], 1):
                print(f"  {i}. {chunk.gene_name} ({chunk.species}) - {score:.3f}")
                print(f"     来源: {chunk.article_title[:50]}...")

        # 生成
        print(f"\n[2/2] 生成答案...\n")
        print("-" * 60)
        answer = self.generator.generate(question, results, stream=stream)
        print("-" * 60)

        return answer

    def interactive(self):
        """交互式问答"""
        print("\n" + "="*60)
        print("基因信息RAG系统 - 交互模式")
        print("输入问题进行查询，输入 'quit' 或 'exit' 退出")
        print("="*60)

        while True:
            try:
                question = input("\n请输入问题: ").strip()
                if not question:
                    continue
                if question.lower() in ['quit', 'exit', 'q']:
                    print("再见！")
                    break

                self.query(question)

            except KeyboardInterrupt:
                print("\n\n已中断")
                break
            except Exception as e:
                print(f"错误: {e}")


def main():
    parser = argparse.ArgumentParser(description="基因信息RAG系统")
    parser.add_argument("-q", "--query", type=str, help="直接查询问题")
    parser.add_argument("-i", "--interactive", action="store_true", help="交互模式")
    parser.add_argument("--build-index", action="store_true", help="强制重建索引")
    parser.add_argument("--no-rerank", action="store_true", help="禁用rerank")
    parser.add_argument("--no-stream", action="store_true", help="禁用流式输出")

    args = parser.parse_args()

    rag = GeneRAG(build_index=args.build_index)

    if args.query:
        rag.query(args.query,
                  use_rerank=not args.no_rerank,
                  stream=not args.no_stream)
    elif args.interactive:
        rag.interactive()
    else:
        # 默认进入交互模式
        rag.interactive()


if __name__ == "__main__":
    main()
