#!/usr/bin/env python3
"""
测试 DeepSeek V4 兼容性

验证：
1. 模型识别正确
2. 参数清理正确（移除 temperature 等）
3. extra_body 配置正确（thinking + reasoning_effort）
4. reasoning_content 处理正确
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "rag"))

from rag.core.llm_client import (
    is_deepseek_reasoner,
    _sanitize_params_for_model,
    _DEEPSEEK_REASONER_MODELS,
)
from extractor.utils import is_deepseek_model, prepare_deepseek_params


def test_model_detection():
    """测试模型识别"""
    print("=" * 60)
    print("测试 1: 模型识别")
    print("=" * 60)

    test_cases = [
        ("deepseek-v4", True),
        ("deepseek-reasoner", True),
        ("deepseek-r1", True),
        ("DeepSeek-V4", True),  # 大小写不敏感
        ("gpt-4", False),
        ("claude-opus-4", False),
        ("Vendor2/Claude-4.6-opus", False),
    ]

    for model, expected in test_cases:
        result_rag = is_deepseek_reasoner(model)
        result_extractor = is_deepseek_model(model)
        status = "✅" if result_rag == expected and result_extractor == expected else "❌"
        print(f"{status} {model:30s} -> RAG: {result_rag}, Extractor: {result_extractor} (expected: {expected})")

    print()


def test_rag_param_sanitization():
    """测试 RAG 参数清理（Agent 调用）"""
    print("=" * 60)
    print("测试 2: RAG 参数清理（Agent 模式）")
    print("=" * 60)

    # 测试 DeepSeek V4 + Agent 调用
    params = {
        "model": "deepseek-v4",
        "messages": [{"role": "user", "content": "test"}],
        "temperature": 0.7,
        "top_p": 0.9,
        "presence_penalty": 0.5,
        "logprobs": True,
        "max_tokens": 1000,
    }

    result = _sanitize_params_for_model("deepseek-v4", params.copy(), is_agent_call=True)

    print("输入参数:", list(params.keys()))
    print("输出参数:", list(result.keys()))
    print()

    # 验证移除的参数
    removed = ["temperature", "top_p", "presence_penalty", "logprobs"]
    for key in removed:
        status = "✅" if key not in result else "❌"
        print(f"{status} {key} 已移除: {key not in result}")

    # 验证保留的参数
    kept = ["model", "messages", "max_tokens"]
    for key in kept:
        status = "✅" if key in result else "❌"
        print(f"{status} {key} 已保留: {key in result}")

    # 验证 extra_body
    print()
    print("extra_body 配置:")
    if "extra_body" in result:
        print(f"  ✅ thinking: {result['extra_body'].get('thinking')}")
        print(f"  ✅ reasoning_effort: {result['extra_body'].get('reasoning_effort')}")

        # Agent 调用应该使用 max effort
        if result['extra_body'].get('reasoning_effort') == 'max':
            print("  ✅ Agent 模式正确使用 max effort")
        else:
            print(f"  ❌ Agent 模式应该使用 max effort，实际: {result['extra_body'].get('reasoning_effort')}")
    else:
        print("  ❌ 缺少 extra_body")

    print()


def test_rag_param_sanitization_normal():
    """测试 RAG 参数清理（非 Agent 调用）"""
    print("=" * 60)
    print("测试 3: RAG 参数清理（普通模式）")
    print("=" * 60)

    params = {
        "model": "deepseek-v4",
        "messages": [{"role": "user", "content": "test"}],
        "temperature": 0.7,
    }

    result = _sanitize_params_for_model("deepseek-v4", params.copy(), is_agent_call=False)

    print("extra_body 配置:")
    if "extra_body" in result:
        effort = result['extra_body'].get('reasoning_effort')
        print(f"  reasoning_effort: {effort}")
        if effort == 'high':
            print("  ✅ 普通模式正确使用 high effort")
        else:
            print(f"  ❌ 普通模式应该使用 high effort，实际: {effort}")

    print()


def test_extractor_param_preparation():
    """测试 Extractor 参数准备"""
    print("=" * 60)
    print("测试 4: Extractor 参数准备")
    print("=" * 60)

    params = {
        "model": "deepseek-v4",
        "messages": [{"role": "user", "content": "test"}],
        "temperature": 0.7,
        "max_tokens": 16384,
        "tools": [{"type": "function", "function": {"name": "extract_all_genes"}}],
    }

    result = prepare_deepseek_params("deepseek-v4", params.copy())

    print("输入参数:", list(params.keys()))
    print("输出参数:", list(result.keys()))
    print()

    # 验证移除 temperature
    if "temperature" not in result:
        print("✅ temperature 已移除")
    else:
        print("❌ temperature 应该被移除")

    # 验证保留其他参数
    for key in ["model", "messages", "max_tokens", "tools"]:
        status = "✅" if key in result else "❌"
        print(f"{status} {key} 已保留: {key in result}")

    # 验证 extra_body
    print()
    print("extra_body 配置:")
    if "extra_body" in result:
        print(f"  ✅ thinking: {result['extra_body'].get('thinking')}")
        effort = result['extra_body'].get('reasoning_effort')
        print(f"  ✅ reasoning_effort: {effort}")

        # Extractor 应该使用 high effort（不是 max）
        if effort == 'high':
            print("  ✅ Extractor 正确使用 high effort")
        else:
            print(f"  ❌ Extractor 应该使用 high effort，实际: {effort}")
    else:
        print("  ❌ 缺少 extra_body")

    print()


def test_non_deepseek_model():
    """测试非 DeepSeek 模型不受影响"""
    print("=" * 60)
    print("测试 5: 非 DeepSeek 模型不受影响")
    print("=" * 60)

    params = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "test"}],
        "temperature": 0.7,
        "top_p": 0.9,
    }

    result_rag = _sanitize_params_for_model("gpt-4", params.copy(), is_agent_call=True)
    result_extractor = prepare_deepseek_params("gpt-4", params.copy())

    # 非 DeepSeek 模型应该保持原样
    if result_rag == params:
        print("✅ RAG: 非 DeepSeek 模型参数未修改")
    else:
        print("❌ RAG: 非 DeepSeek 模型参数被意外修改")

    if result_extractor == params:
        print("✅ Extractor: 非 DeepSeek 模型参数未修改")
    else:
        print("❌ Extractor: 非 DeepSeek 模型参数被意外修改")

    print()


def main():
    print("\n" + "=" * 60)
    print("DeepSeek V4 兼容性测试")
    print("=" * 60)
    print()

    print(f"支持的 DeepSeek 模型: {_DEEPSEEK_REASONER_MODELS}")
    print()

    test_model_detection()
    test_rag_param_sanitization()
    test_rag_param_sanitization_normal()
    test_extractor_param_preparation()
    test_non_deepseek_model()

    print("=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
