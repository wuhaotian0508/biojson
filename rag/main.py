#!/usr/bin/env python3
"""
主程序入口 - 命令行交互模式
"""
import argparse
# 使用简单检索器（TF-IDF）
from simple_retriever import SimpleRetriever as Retriever
from generator import Generator


def interactive_mode():
    """交互模式"""
    print("=" * 80)
    print("植物营养代谢基因问答系统")
    print("=" * 80)
    print("\n初始化系统...")

    # 初始化
    retriever = Retriever()
    retriever.build_index()
    generator = Generator()

    print("\n系统就绪！输入问题开始查询，输入 'exit' 或 'quit' 退出\n")

    while True:
        try:
            query = input("\n请输入问题: ").strip()

            if not query:
                continue

            if query.lower() in ['exit', 'quit', 'q']:
                print("\n再见！")
                break

            # 检索
            print("\n检索中...")
            chunks = retriever.retrieve(query)
            print(f"检索到 {len(chunks)} 个相关文献")

            # 显示来源
            print("\n相关文献:")
            for i, (chunk, score) in enumerate(chunks, 1):
                print(f"  {i}. [{chunk.paper_title} | {chunk.gene_name}] (相关度: {score:.3f})")

            # 生成答案
            print("\n生成答案...\n")
            print("-" * 80)

            for text in generator.generate(query, chunks, stream=True):
                print(text, end='', flush=True)

            print("\n" + "-" * 80)

        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"\n错误: {e}")


def single_query(query: str):
    """单次查询模式"""
    print(f"查询: {query}\n")

    # 初始化
    retriever = Retriever()
    retriever.build_index()
    generator = Generator()

    # 检索
    print("检索中...")
    chunks = retriever.retrieve(query)
    print(f"检索到 {len(chunks)} 个相关文献\n")

    # 显示来源
    print("相关文献:")
    for i, (chunk, score) in enumerate(chunks, 1):
        print(f"  {i}. [{chunk.paper_title} | {chunk.gene_name}] (相关度: {score:.3f})")

    # 生成答案
    print("\n答案:")
    print("-" * 80)

    for text in generator.generate(query, chunks, stream=True):
        print(text, end='', flush=True)

    print("\n" + "-" * 80)


def main():
    parser = argparse.ArgumentParser(description="植物营养代谢基因问答系统")
    parser.add_argument("-i", "--interactive", action="store_true",
                       help="交互模式")
    parser.add_argument("-q", "--query", type=str,
                       help="单次查询")
    parser.add_argument("--rebuild-index", action="store_true",
                       help="重建索引")

    args = parser.parse_args()

    # 重建索引
    if args.rebuild_index:
        print("重建索引...")
        retriever = Retriever()
        retriever.build_index(force_rebuild=True)
        print("索引重建完成！")
        return

    # 交互模式
    if args.interactive:
        interactive_mode()
    # 单次查询
    elif args.query:
        single_query(args.query)
    # 默认交互模式
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
