#!/usr/bin/env python3
"""
RAG API 测试脚本

用于验证 API Server 各端点是否正常工作。
提供两种测试方式：
  1. 同步查询 - 等待完整结果后一次性显示
  2. 流式查询 - 实时逐字显示输出（体验更好）

用法:
  python test_api.py --query "番茄中番茄红素合成的关键基因有哪些？"
  python test_api.py --query "..." --stream  # 流式输出
  python test_api.py --query "..." --depth   # 深度模式（更多工具调用轮次）
"""
import argparse
import json
import requests
import sys


def test_sync(base_url: str, query: str, model_id: str = "primary", use_depth: bool = False):
    """
    测试同步查询端点 (/api/query)。
    发送请求后阻塞等待完整结果，适合自动化测试场景。
    完成后格式化输出答案、工具调用记录和引用来源。
    """
    # 打印查询概览，方便确认测试参数
    print(f"\n{'='*60}")
    print(f"查询: {query}")
    print(f"模式: {'深度' if use_depth else '普通'}")
    print(f"{'='*60}\n")

    url = f"{base_url}/api/query"
    payload = {
        "query": query,
        "model_id": model_id,
        "use_depth": use_depth,
    }

    try:
        # timeout=300 因为复杂查询可能涉及多轮工具调用，需要较长等待时间
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        result = response.json()

        # 输出主要答案
        print("回答:")
        print("-" * 60)
        print(result["answer"])
        print("-" * 60)

        # 如果 Agent 调用了工具，显示调用详情（便于调试工具选择是否合理）
        if result.get("tool_calls"):
            print(f"\n工具调用 ({result['steps']} 步):")
            for i, tc in enumerate(result["tool_calls"], 1):
                print(f"  {i}. {tc['tool']}")
                if tc.get("args"):
                    # ensure_ascii=False 确保中文参数正常显示
                    print(f"     参数: {json.dumps(tc['args'], ensure_ascii=False)}")

        # 显示引用来源，验证 RAG 检索是否正常命中相关文献
        if result.get("sources"):
            print(f"\n引用来源 ({len(result['sources'])} 条):")
            for i, src in enumerate(result["sources"], 1):
                print(f"  {i}. {src.get('title', 'N/A')}")
                if src.get("doi"):
                    print(f"     DOI: {src['doi']}")

    except requests.exceptions.RequestException as e:
        # 网络层错误：连接拒绝、超时等
        print(f"请求失败: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # 其他未预期的错误
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


def test_stream(base_url: str, query: str, model_id: str = "primary", use_depth: bool = False):
    """
    测试流式查询端点 (/api/query/stream)。
    通过 SSE 逐个接收事件并实时渲染到终端，
    模拟前端流式显示的效果，验证流式推送链路是否完整。
    """
    print(f"\n{'='*60}")
    print(f"查询: {query}")
    print(f"模式: {'深度' if use_depth else '普通'} (流式)")
    print(f"{'='*60}\n")

    url = f"{base_url}/api/query/stream"
    payload = {
        "query": query,
        "model_id": model_id,
        "use_depth": use_depth,
    }

    try:
        # stream=True 告诉 requests 不要缓冲完整响应，而是按块接收
        response = requests.post(url, json=payload, stream=True, timeout=300)
        response.raise_for_status()

        tool_count = 0  # 工具调用计数器
        sources = []    # 收集引用来源，在流结束后统一显示

        # 逐行解析 SSE 数据流
        for line in response.iter_lines():
            if not line:
                continue

            line = line.decode("utf-8")
            # SSE 协议中数据行以 "data: " 开头，其他行（如空行、注释）跳过
            if not line.startswith("data: "):
                continue

            try:
                event = json.loads(line[6:])  # 去掉 "data: " 前缀后解析 JSON
                event_type = event.get("type")

                if event_type == "text":
                    # 文本片段：实时打印，end="" 避免换行，flush=True 立即输出
                    print(event.get("data", ""), end="", flush=True)

                elif event_type == "tool_call":
                    # 工具调用开始：插入工具调用提示，方便观察 Agent 的决策过程
                    tool_count += 1
                    tool_name = event.get("tool")
                    print(f"\n\n[工具 {tool_count}] {tool_name}", flush=True)

                elif event_type == "tool_result":
                    # 工具调用结果摘要：截取前 100 字符避免输出过长
                    summary = event.get("summary", "")
                    if summary:
                        print(f"  → {summary[:100]}...", flush=True)

                elif event_type == "sources":
                    # 引用来源事件：暂存，等流结束后再格式化输出
                    sources = event.get("data", [])

                elif event_type == "done":
                    # 查询完成：输出引用来源汇总
                    print("\n")
                    if sources:
                        print(f"\n引用来源 ({len(sources)} 条):")
                        for i, src in enumerate(sources, 1):
                            print(f"  {i}. {src.get('title', 'N/A')}")

                elif event_type == "error":
                    # 服务端通过 SSE 通道推送的错误
                    print(f"\n错误: {event.get('data')}", file=sys.stderr)
                    sys.exit(1)

            except json.JSONDecodeError:
                # 忽略无法解析的行（可能是服务端日志输出等）
                continue

    except requests.exceptions.RequestException as e:
        print(f"\n请求失败: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}", file=sys.stderr)
        sys.exit(1)


def test_health(base_url: str):
    """
    测试健康检查端点 (/api/health)。
    在执行查询前调用，确保服务已启动且各组件初始化完成。
    返回 True/False 供调用方判断是否继续测试。
    """
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        response.raise_for_status()
        result = response.json()

        print("API 健康检查通过")
        print(f"  - 文档块数: {result['total_chunks']}")
        print(f"  - 可用工具: {', '.join(result['tools'])}")
        print(f"  - 系统技能: {result['skills']} 个")
        return True

    except Exception as e:
        print(f"API 不可用: {e}", file=sys.stderr)
        return False


def main():
    """
    脚本入口函数。
    解析命令行参数，按顺序执行：
    1. 健康检查（确认服务可用）
    2. 根据 --stream 标志选择同步或流式查询
    """
    parser = argparse.ArgumentParser(description="RAG API 测试脚本")
    parser.add_argument("--url", default="http://localhost:8000", help="API 地址")
    parser.add_argument("--query", "-q", help="查询文本")
    parser.add_argument("--stream", "-s", action="store_true", help="使用流式输出")
    parser.add_argument("--depth", "-d", action="store_true", help="启用深度模式")
    parser.add_argument("--model", "-m", default="primary", help="模型 ID")
    parser.add_argument("--health", action="store_true", help="仅检查健康状态")

    args = parser.parse_args()

    # 仅做健康检查时不需要查询文本
    if args.health:
        test_health(args.url)
        return

    # 查询模式下必须提供查询文本
    if not args.query:
        print("请提供查询文本 (--query)", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # 先确认 API 服务可用，避免等待超时后才发现服务未启动
    if not test_health(args.url):
        sys.exit(1)

    # 根据用户选择执行同步或流式查询
    if args.stream:
        test_stream(args.url, args.query, args.model, args.depth)
    else:
        test_sync(args.url, args.query, args.model, args.depth)


if __name__ == "__main__":
    main()
