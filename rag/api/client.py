"""
RAG API 客户端库

提供 Python 客户端封装，方便在其他项目中调用 RAG API。

示例:
    from rag.api.client import RAGClient

    client = RAGClient("http://localhost:8000")
    result = client.query("番茄中番茄红素合成的关键基因有哪些？")
    print(result["answer"])
"""
import requests
from typing import Optional, Iterator, Dict, Any


class RAGClient:
    """
    RAG API 客户端类。
    封装了与 RAG API Server 的所有交互逻辑，
    提供简洁的 Python 接口，隐藏 HTTP 请求细节。
    """

    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 300):
        """
        初始化客户端

        参数:
            base_url: API 服务地址（自动去除末尾斜杠，避免拼接 URL 时出现双斜杠）
            timeout: 请求超时时间（秒）。RAG 查询可能涉及多轮工具调用，
                    设置较长的超时时间（5分钟）避免复杂查询被中断。
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def health(self) -> Dict[str, Any]:
        """
        健康检查。
        返回服务状态、文档块数量、可用工具等信息。
        可用于启动后验证服务是否就绪，或监控系统运行状态。
        """
        response = requests.get(f"{self.base_url}/api/health", timeout=10)
        response.raise_for_status()  # 非 2xx 状态码会抛出异常
        return response.json()

    def list_tools(self) -> Dict[str, Any]:
        """
        列出所有可用工具。
        返回工具名称和描述，方便了解当前系统支持哪些能力。
        """
        response = requests.get(f"{self.base_url}/api/tools", timeout=10)
        response.raise_for_status()
        return response.json()

    def query(
        self,
        query: str,
        model_id: str = "primary",
        use_depth: bool = False,
        max_steps: int = 20,
    ) -> Dict[str, Any]:
        """
        同步查询（等待完整结果）。
        适合批量测试或对延迟不敏感的场景。

        参数:
            query: 查询文本
            model_id: 模型 ID（primary 使用主力模型，fallback 使用备用模型）
            use_depth: 是否启用深度模式（更多轮工具调用，适合复杂问题）
            max_steps: 最大工具调用步数（防止无限循环）

        返回:
            {
                "answer": str,          # 最终答案文本
                "sources": list,        # 引用来源列表
                "tool_calls": list,     # 工具调用记录
                "steps": int            # 实际执行步数
            }
        """
        response = requests.post(
            f"{self.base_url}/api/query",
            json={
                "query": query,
                "model_id": model_id,
                "use_depth": use_depth,
                "max_steps": max_steps,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def query_stream(
        self,
        query: str,
        model_id: str = "primary",
        use_depth: bool = False,
        max_steps: int = 20,
    ) -> Iterator[Dict[str, Any]]:
        """
        流式查询（实时返回事件）。
        通过 Server-Sent Events (SSE) 协议逐个接收事件，
        适合需要实时展示中间结果的场景（如前端逐字显示回答）。

        参数:
            query: 查询文本
            model_id: 模型 ID
            use_depth: 是否启用深度模式
            max_steps: 最大工具调用步数

        Yields:
            事件字典，格式: {"type": str, "data": Any, ...}
            可能的事件类型：
            - text: LLM 生成的文本片段
            - tool_call: 工具调用开始
            - tool_result: 工具调用结果
            - sources: 引用来源
            - done: 查询完成
            - error: 出错
        """
        import json

        response = requests.post(
            f"{self.base_url}/api/query/stream",
            json={
                "query": query,
                "model_id": model_id,
                "use_depth": use_depth,
                "max_steps": max_steps,
            },
            stream=True,  # 启用流式接收，避免等待完整响应
            timeout=self.timeout,
        )
        response.raise_for_status()

        # 逐行解析 SSE 数据流
        for line in response.iter_lines():
            if not line:
                continue  # 跳过空行（SSE 协议用空行分隔事件）

            line = line.decode("utf-8")
            if not line.startswith("data: "):
                continue  # 跳过非数据行（SSE 还支持 event:、id: 等字段）

            try:
                # 去掉 "data: " 前缀，解析 JSON
                event = json.loads(line[6:])
                yield event
            except json.JSONDecodeError:
                # 忽略无效 JSON（可能是服务端日志或其他干扰信息）
                continue


# ------------------------------------------------------------------
# 便捷函数（快速调用，无需创建客户端实例）
# ------------------------------------------------------------------
def query(
    query_text: str,
    base_url: str = "http://localhost:8000",
    use_depth: bool = False,
) -> str:
    """
    快速查询函数（返回答案文本）。
    适合简单脚本或 Jupyter Notebook 中快速测试。

    示例:
        from rag.api.client import query
        answer = query("番茄中番茄红素合成的关键基因有哪些？")
        print(answer)
    """
    client = RAGClient(base_url)
    result = client.query(query_text, use_depth=use_depth)
    return result["answer"]
