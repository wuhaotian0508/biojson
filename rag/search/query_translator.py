"""
查询翻译模块 — LLM 提取关键术语并翻译

策略：
  用 LLM 提取查询中的关键生物学术语（基因、化合物、通路、过程等），
  并输出对应的英文术语，追加到原始查询中。

用法：
    from search.query_translator import translate_query_terms
    enhanced = await translate_query_terms("α-番茄碱在番茄果实中的积累机制")
    # → "α-番茄碱 α-tomatine 番茄 tomato 果实 fruit 积累 accumulation 机制 mechanism"
"""
import re
import json
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

# LLM API 配置（从环境变量或配置文件读取）
_API_KEY: Optional[str] = None
_BASE_URL: Optional[str] = None
_MODEL: Optional[str] = None


def configure_llm(api_key: str, base_url: str, model: str = "gpt-4o-mini"):
    """配置 LLM API 参数（在应用启动时调用）"""
    global _API_KEY, _BASE_URL, _MODEL
    _API_KEY = api_key
    _BASE_URL = base_url
    _MODEL = model


async def _extract_and_translate_with_llm(query: str) -> dict[str, str]:
    """
    用 LLM 提取关键术语并翻译成英文。

    返回: {原术语: 英文翻译} 的字典
    """
    if not _API_KEY or not _BASE_URL:
        logger.warning("LLM API 未配置，跳过术语翻译")
        return {}

    prompt = f"""从以下生物学查询中提取关键术语（基因名、化合物名、通路名、生物学过程、物种名等），并翻译成对应的英文术语。

查询: {query}

要求:
1. 提取所有专业术语，忽略"的"、"在"、"中"、"如何"等虚词
2. 中文术语翻译成英文，英文术语保持原样
3. 返回 JSON 格式: {{"术语": "English term", ...}}
4. 如果查询已经是纯英文，返回空对象 {{}}

示例1:
查询: 番茄果实中类胡萝卜素的合成途径
输出: {{"番茄": "tomato", "果实": "fruit", "类胡萝卜素": "carotenoid", "合成途径": "biosynthesis pathway"}}

示例2:
查询: CRISPR 编辑提高玉米赖氨酸含量
输出: {{"CRISPR": "CRISPR", "编辑": "editing", "玉米": "maize", "赖氨酸": "lysine", "含量": "content"}}

示例3:
查询: vitamin C biosynthesis in rice
输出: {{}}

现在处理上面的查询，只返回 JSON，不要其他内容:"""

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": _MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 500,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()

            # 提取 JSON（可能被 markdown 代码块包裹）
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return {}

    except Exception as e:
        logger.warning(f"LLM 术语翻译失败: {e}")
        return {}


async def translate_query_terms(query: str) -> str:
    """
    用 LLM 提取关键术语并追加英文翻译。

    参数:
        query: 原始查询

    返回:
        增强后的查询（原文 + 英文术语）
    """
    if not _API_KEY:
        logger.warning("LLM API 未配置，返回原始查询")
        return query

    # 用 LLM 提取术语并翻译
    translations = await _extract_and_translate_with_llm(query)

    if not translations:
        return query

    # 将翻译追加到原查询中
    enhanced = query
    for term, en_term in translations.items():
        # 跳过英文翻译已经在 query 中的（避免重复）
        if en_term.lower() in enhanced.lower():
            continue
        # 追加翻译（在术语后加空格，避免粘连）
        if term in enhanced:
            enhanced = enhanced.replace(term, f"{term} {en_term} ", 1)

    return enhanced.strip()  # 去除末尾多余空格


if __name__ == "__main__":
    import asyncio
    import os

    # 配置 LLM（从环境变量读取）
    configure_llm(
        api_key=os.getenv("API_KEY", ""),
        base_url=os.getenv("BASE_URL", "https://api.openai.com/v1"),
        model=os.getenv("MODEL", "gpt-4o-mini"),
    )

    test_queries = [
        "α-番茄碱在番茄果实中的积累机制",
        "水稻耐旱转录因子的调控网络",
        "CRISPR 编辑提高玉米赖氨酸含量",
        "类胡萝卜素合成通路关键酶",
    ]

    async def test():
        for q in test_queries:
            print(f"\n原始查询: {q}")
            enhanced = await translate_query_terms(q)
            print(f"增强查询: {enhanced}")
            print(f"变化: {'✓' if enhanced != q else '✗'}")

    asyncio.run(test())
