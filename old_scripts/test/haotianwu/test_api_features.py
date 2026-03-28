"""
test_api_features.py
测试 API 代理支持的结构化输出功能

测试项目:
1. response_format={"type": "json_object"} — JSON 模式
2. tools / function_calling — 工具调用
3. assistant prefill — 预填充技巧
4. 普通 JSON 提取（基线）
"""

import os
import json
import sys
from openai import OpenAI
from dotenv import load_dotenv

# 加载 .env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

MODEL = os.getenv("MODEL", "Vendor2/Claude-4.6-opus")

# 通用测试 prompt
TEST_USER_MSG = "Extract the gene info from this sentence: 'The ZmPSY1 gene in Zea mays encodes phytoene synthase (EC 2.5.1.32) and increases β-carotene content by 2.3-fold in maize endosperm.' Return a JSON with keys: gene_name, species, enzyme, ec_number, effect."

SEPARATOR = "=" * 60


def test_1_json_mode():
    """测试 1: response_format={"type": "json_object"}"""
    print(f"\n{SEPARATOR}")
    print("🧪 测试 1: response_format={{\"type\": \"json_object\"}}")
    print(SEPARATOR)
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Always respond in valid JSON."},
                {"role": "user", "content": TEST_USER_MSG},
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=500,
        )
        result = response.choices[0].message.content
        print(f"✅ 支持！返回内容:\n{result}")
        # 验证是否是合法 JSON
        try:
            parsed = json.loads(result)
            print(f"✅ JSON 解析成功: {json.dumps(parsed, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError:
            print(f"⚠️  返回了内容但不是合法 JSON")
        return True
    except Exception as e:
        print(f"❌ 不支持: {e}")
        return False


def test_2_function_calling():
    """测试 2: tools / function_calling"""
    print(f"\n{SEPARATOR}")
    print("🧪 测试 2: tools / function_calling")
    print(SEPARATOR)

    tools = [
        {
            "type": "function",
            "function": {
                "name": "extract_gene_info",
                "description": "Extract gene information from text",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "gene_name": {"type": "string", "description": "Gene symbol"},
                        "species": {"type": "string", "description": "Species name"},
                        "enzyme": {"type": "string", "description": "Enzyme name"},
                        "ec_number": {"type": "string", "description": "EC number"},
                        "effect": {"type": "string", "description": "Effect description"},
                    },
                    "required": ["gene_name", "species", "enzyme", "ec_number", "effect"],
                },
            },
        }
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a gene extraction assistant."},
                {"role": "user", "content": TEST_USER_MSG},
            ],
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "extract_gene_info"}},
            temperature=0,
            max_tokens=500,
        )
        msg = response.choices[0].message
        if msg.tool_calls:
            tc = msg.tool_calls[0]
            print(f"✅ 支持！工具调用: {tc.function.name}")
            args = json.loads(tc.function.arguments)
            print(f"✅ 参数: {json.dumps(args, indent=2, ensure_ascii=False)}")
        else:
            print(f"⚠️  返回了内容但没有 tool_calls:")
            print(f"   content: {msg.content[:300] if msg.content else 'None'}")
        return True
    except Exception as e:
        print(f"❌ 不支持: {e}")
        return False


def test_3_prefill():
    """测试 3: assistant prefill（预填充技巧）"""
    print(f"\n{SEPARATOR}")
    print("🧪 测试 3: assistant prefill（预填充 JSON 开头）")
    print(SEPARATOR)
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You extract gene information and return ONLY valid JSON, no extra text."},
                {"role": "user", "content": TEST_USER_MSG},
                {"role": "assistant", "content": "{"},  # 预填充
            ],
            temperature=0,
            max_tokens=500,
        )
        raw = response.choices[0].message.content
        # 补上开头的 {
        full_json = "{" + raw
        print(f"✅ 返回内容（补上 {{ 后）:\n{full_json[:500]}")
        try:
            parsed = json.loads(full_json)
            print(f"✅ JSON 解析成功: {json.dumps(parsed, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError:
            print(f"⚠️  补上 {{ 后仍不是合法 JSON，尝试原始内容...")
            try:
                parsed = json.loads(raw)
                print(f"✅ 原始内容就是合法 JSON: {json.dumps(parsed, indent=2, ensure_ascii=False)}")
            except json.JSONDecodeError:
                print(f"⚠️  都不是合法 JSON")
        return True
    except Exception as e:
        print(f"❌ 不支持: {e}")
        return False


def test_4_baseline():
    """测试 4: 普通方式（基线对照）"""
    print(f"\n{SEPARATOR}")
    print("🧪 测试 4: 普通请求（基线对照）")
    print(SEPARATOR)
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You extract gene information. Return ONLY a JSON object, no explanation."},
                {"role": "user", "content": TEST_USER_MSG},
            ],
            temperature=0,
            max_tokens=500,
        )
        raw = response.choices[0].message.content
        print(f"✅ 返回内容:\n{raw[:500]}")

        # 尝试解析
        try:
            parsed = json.loads(raw)
            print(f"✅ 直接就是合法 JSON")
        except json.JSONDecodeError:
            # 尝试提取 ```json ... ```
            import re
            match = re.search(r'```json\s*(.*?)\s*```', raw, re.DOTALL)
            if match:
                parsed = json.loads(match.group(1))
                print(f"✅ 从 markdown 代码块提取到 JSON")
            else:
                match = re.search(r'(\{.*\})', raw, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(1))
                    print(f"✅ 从花括号提取到 JSON")
                else:
                    print(f"⚠️  无法提取到 JSON")
        return True
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def main():
    print(f"\n{'═' * 60}")
    print(f"🔬 API 代理功能测试")
    print(f"   模型: {MODEL}")
    print(f"   Base URL: {os.getenv('OPENAI_BASE_URL')}")
    print(f"{'═' * 60}")

    results = {}

    # 测试 4 先跑（基线），确认 API 基本可用
    results["baseline"] = test_4_baseline()

    if not results["baseline"]:
        print("\n❌ 基线测试失败，API 连接可能有问题，跳过其他测试。")
        return

    results["json_mode"] = test_1_json_mode()
    results["function_calling"] = test_2_function_calling()
    results["prefill"] = test_3_prefill()

    # 汇总
    print(f"\n{'═' * 60}")
    print(f"📊 测试结果汇总")
    print(f"{'═' * 60}")
    labels = {
        "baseline": "普通请求（基线）",
        "json_mode": "JSON 模式 (response_format)",
        "function_calling": "工具调用 (tools/function_calling)",
        "prefill": "预填充技巧 (assistant prefill)",
    }
    for key, label in labels.items():
        status = "✅ 支持" if results.get(key) else "❌ 不支持"
        print(f"  {status}  {label}")
    print(f"{'═' * 60}")

    # 推荐方案
    print(f"\n💡 推荐方案:")
    if results.get("function_calling"):
        print("  👉 首选: function_calling（最可靠的结构化输出）")
    if results.get("json_mode"):
        print("  👉 可用: JSON 模式（API 强制 JSON 输出）")
    if results.get("prefill"):
        print("  👉 可用: prefill 技巧（简单有效）")
    if not any([results.get("function_calling"), results.get("json_mode"), results.get("prefill")]):
        print("  👉 建议: 保留当前正则提取方式 + 加 json-repair 兜底")


if __name__ == "__main__":
    main()
