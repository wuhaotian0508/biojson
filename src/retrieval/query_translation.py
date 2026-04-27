from __future__ import annotations

import json
import logging
import re
from collections.abc import Awaitable, Callable

import httpx

logger = logging.getLogger(__name__)


class QueryTranslator:
    def __init__(self, call_llm: Callable[[str], Awaitable[str]] | None):
        self._call_llm = call_llm

    @classmethod
    def from_openai_compatible(
        cls,
        *,
        api_key: str,
        base_url: str,
        model: str = "gpt-4o-mini",
    ) -> "QueryTranslator":
        async def call_llm(prompt: str) -> str:
            if not api_key or not base_url:
                return "{}"
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{base_url.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 500,
                    },
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"].strip()

        return cls(call_llm=call_llm)

    async def translate_query_terms(self, query: str) -> str:
        if self._call_llm is None:
            return query
        prompt = _build_prompt(query)
        try:
            content = await self._call_llm(prompt)
            match = re.search(r"\{.*\}", content, re.DOTALL)
            translations = json.loads(match.group(0)) if match else {}
        except Exception as exc:
            logger.warning("LLM term translation failed: %s", exc)
            return query
        if not translations:
            return query
        enhanced = query
        for term, english in translations.items():
            if str(english).lower() in enhanced.lower():
                continue
            if term in enhanced:
                enhanced = enhanced.replace(term, f"{term} {english} ", 1)
        return enhanced.strip()


def _build_prompt(query: str) -> str:
    return f"""从以下生物学查询中提取关键术语（基因名、化合物名、通路名、生物学过程、物种名等），并翻译成对应的英文术语。

查询: {query}

要求:
1. 提取所有专业术语，忽略"的"、"在"、"中"、"如何"等虚词
2. 中文术语翻译成英文，英文术语保持原样
3. 返回 JSON 格式: {{"术语": "English term", ...}}
4. 如果查询已经是纯英文，返回空对象 {{}}

现在处理上面的查询，只返回 JSON，不要其他内容:"""


_TRANSLATOR = QueryTranslator(call_llm=None)


def configure_llm(api_key: str, base_url: str, model: str = "gpt-4o-mini"):
    global _TRANSLATOR
    _TRANSLATOR = QueryTranslator.from_openai_compatible(
        api_key=api_key,
        base_url=base_url,
        model=model,
    )


async def translate_query_terms(query: str) -> str:
    return await _TRANSLATOR.translate_query_terms(query)
