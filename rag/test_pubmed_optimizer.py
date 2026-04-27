#!/usr/bin/env python3
"""
测试 PubMed 查询优化功能
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from rag.tools.pubmed_search import configure_query_optimizer, _optimize_pubmed_query

# 加载环境变量
load_dotenv(Path(__file__).parent.parent / ".env")

# 配置 LLM
configure_query_optimizer(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    model="gpt-4o-mini",
)


async def test_optimization():
    """测试不同类型的查询优化"""
    test_cases = [
        # 过长的查询（Agent 生成的）
        "tomato potato eggplant 25S 25R steroidal glycoalkaloids alpha-tomatine alpha-solasonine alpha-solamargine biological activity",

        # 中文查询
        "番茄中α-番茄碱的生物合成途径",

        # 复杂查询
        "茄科植物中25S和25R构型生物碱的生物学功能差异",

        # 基因名查询
        "GAME8 基因在番茄生物碱合成中的作用",

        # 已经优化的查询（应该保持不变）
        "CRISPR AND rice AND (iron OR Fe)",

        # 综述查询
        "类胡萝卜素合成通路的研究进展",
    ]

    print("=" * 80)
    print("PubMed 查询优化测试")
    print("=" * 80)

    for i, query in enumerate(test_cases, 1):
        print(f"\n[测试 {i}]")
        print(f"原始查询: {query}")
        print(f"查询长度: {len(query.split())} 词")

        try:
            optimized = await _optimize_pubmed_query(query)
            print(f"优化查询: {optimized}")
            print(f"优化长度: {len(optimized.split())} 词")

            if optimized == query:
                print("状态: 无变化（已经是优化格式）")
            else:
                reduction = len(query.split()) - len(optimized.split())
                print(f"状态: ✓ 已优化（减少 {reduction} 词）")

        except Exception as e:
            print(f"错误: {e}")

        print("-" * 80)


if __name__ == "__main__":
    asyncio.run(test_optimization())
