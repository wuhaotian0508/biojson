#!/usr/bin/env python3
"""
测试查询翻译功能
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from rag.search.query_translator import configure_llm, translate_query_terms

# 加载环境变量
load_dotenv(Path(__file__).parent.parent / ".env")

# 配置 LLM
configure_llm(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    model="gpt-4o-mini",
)


async def test_translation():
    """测试不同类型的查询"""
    test_cases = [
        # 纯中文查询
        "番茄果实中类胡萝卜素的合成途径",

        # 混合查询
        "CRISPR 编辑提高玉米赖氨酸含量",

        # 包含希腊字母
        "α-番茄碱在番茄果实中的积累机制",

        # 复杂生物学查询
        "水稻耐旱转录因子 DREB 的调控网络",

        # 纯英文查询（应该返回原样）
        "vitamin C biosynthesis in rice",

        # 基因名 + 功能
        "OsNAS2 基因在水稻铁生物强化中的作用",
    ]

    print("=" * 80)
    print("查询翻译测试")
    print("=" * 80)

    for i, query in enumerate(test_cases, 1):
        print(f"\n[测试 {i}]")
        print(f"原始查询: {query}")

        try:
            enhanced = await translate_query_terms(query)
            print(f"增强查询: {enhanced}")

            if enhanced == query:
                print("状态: 无变化（可能已是英文或 API 未配置）")
            else:
                print("状态: ✓ 已增强")

        except Exception as e:
            print(f"错误: {e}")

        print("-" * 80)


if __name__ == "__main__":
    asyncio.run(test_translation())
