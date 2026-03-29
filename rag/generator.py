"""
生成器 - 使用 LLM 生成答案，支持流式输出和来源标注
"""
from typing import List, Tuple, Iterator
import requests
from data_loader import GeneChunk
import config


class Generator:
    """LLM 生成器"""

    def __init__(self):
        self.api_key = config.API_KEY
        self.base_url = config.BASE_URL
        self.model = config.LLM_MODEL
        self.system_prompt = config.SYSTEM_PROMPT

    def generate(self, query: str, chunks: List[Tuple[GeneChunk, float]],
                stream: bool = False) -> Iterator[str] | str:
        """生成答案"""
        # 构建上下文
        context = self._build_context(chunks)

        # 构建提示词
        user_prompt = f"""基于以下文献信息回答问题：

{context}

问题：{query}

请基于上述文献信息回答，每条信息都要用 [文章名 | 基因名] 格式标注来源。"""

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        if stream:
            return self._generate_stream(messages)
        else:
            return self._generate_sync(messages)

    def _build_context(self, chunks: List[Tuple[GeneChunk, float]]) -> str:
        """构建上下文"""
        context_parts = []

        for i, (chunk, score) in enumerate(chunks, 1):
            context_parts.append(
                f"【文献{i}】\n"
                f"来源：{chunk.paper_title} | 基因：{chunk.gene_name}\n"
                f"相关度：{score:.3f}\n"
                f"\n{chunk.content}\n"
                f"{'-' * 80}\n"
            )

        return "\n".join(context_parts)

    def _generate_sync(self, messages: List[dict]) -> str:
        """同步生成"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 2000
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            json=data,
            headers=headers
        )
        response.raise_for_status()

        return response.json()["choices"][0]["message"]["content"]

    def _generate_stream(self, messages: List[dict]) -> Iterator[str]:
        """流式生成"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 2000
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            json=data,
            headers=headers,
            stream=True
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    line = line[6:]
                    if line == '[DONE]':
                        break

                    try:
                        import json
                        chunk = json.loads(line)
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta:
                                yield delta['content']
                    except json.JSONDecodeError:
                        continue


if __name__ == "__main__":
    from simple_retriever import SimpleRetriever

    # 初始化
    retriever = SimpleRetriever()
    retriever.build_index()
    generator = Generator()

    # 测试查询
    query = "MYB65 基因的功能是什么？"

    print(f"查询: {query}\n")
    print("检索中...")
    chunks = retriever.retrieve(query)

    print(f"检索到 {len(chunks)} 个相关文献\n")
    print("生成答案...\n")

    # 流式输出
    for text in generator.generate(query, chunks, stream=True):
        print(text, end='', flush=True)

    print("\n")
