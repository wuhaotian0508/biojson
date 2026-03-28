"""
test_function_calling.py

测试主 API 是否支持 function calling 返回 array of objects。
测试 1：简单 schema（4个已知 items）
测试 2：真实 classify_genes schema + 论文摘要片段
"""

import os
import json
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../scripts"))

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

# ── 客户端 ──────────────────────────────────────────────────────────────────
primary_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)
PRIMARY_MODEL = os.getenv("MODEL", "Vendor2/Claude-4.6-opus")

fallback_client = None
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "")
if os.getenv("FALLBACK_API_KEY") and os.getenv("FALLBACK_BASE_URL"):
    fallback_client = OpenAI(
        api_key=os.getenv("FALLBACK_API_KEY"),
        base_url=os.getenv("FALLBACK_BASE_URL"),
    )

# ── 测试 1：简单 schema ─────────────────────────────────────────────────────
SIMPLE_TOOL = {
    "type": "function",
    "function": {
        "name": "test_array_of_objects",
        "description": "Test if the model can return an array of objects in tool call arguments.",
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "description": "A list of items",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "category": {"type": "string", "enum": ["A", "B", "C"]},
                            "value": {"type": "number"}
                        },
                        "required": ["name", "category"]
                    }
                }
            },
            "required": ["items"]
        }
    }
}

SIMPLE_PROMPT = """
Extract the following items:
- Apple: category A, value 1.5
- Banana: category B, value 2.0
- Cherry: category A, value 0.5
- Date: category C, value 3.0

Call test_array_of_objects with all items.
"""

# ── 测试 2：真实 classify_genes schema + 真实论文摘要 ──────────────────────
CLASSIFY_TOOL = {
    "type": "function",
    "function": {
        "name": "classify_genes",
        "description": "Classify all core genes from the Results section into categories.",
        "parameters": {
            "type": "object",
            "properties": {
                "Title": {"type": "string", "description": "Paper title"},
                "Journal": {"type": "string"},
                "DOI": {"type": "string"},
                "genes": {
                    "type": "array",
                    "description": "List of core genes with their categories",
                    "items": {
                        "type": "object",
                        "properties": {
                            "Gene_Name": {
                                "type": "string",
                                "description": "Gene symbol (e.g. CHS, MYB12)"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["Common", "Pathway", "Regulation"],
                                "description": "Common=gene with nutrient data; Pathway=biosynthesis enzyme; Regulation=transcription factor"
                            }
                        },
                        "required": ["Gene_Name", "category"]
                    }
                }
            },
            "required": ["Title", "genes"]
        }
    }
}

PAPER_ABSTRACT = """
# Engineering Flavonoid Biosynthesis in Tomato

## Results

### Overexpression of CHS increases flavonol content
We overexpressed the chalcone synthase gene *CHS* in tomato fruits. 
Transgenic lines showed 3-fold increase in naringenin chalcone levels compared to wild type.
Western blot analysis confirmed CHS protein accumulation in fruit pericarp.

### CHI and F3H act downstream of CHS
Chalcone isomerase (*CHI*) converts naringenin chalcone to naringenin.
Flavanone 3-hydroxylase (*F3H*) further converts naringenin to dihydrokaempferol.
Double overexpression of CHS+CHI resulted in 5-fold increase in quercetin glycosides.

### MYB12 activates flavonol biosynthesis genes
The transcription factor *MYB12* was shown to directly activate CHS, CHI, and F3H promoters.
Overexpression of MYB12 alone was sufficient to increase total flavonols by 8-fold.
MYB12 belongs to the R2R3-MYB family of transcription factors.

### FLS1 controls flavonol accumulation
Flavonol synthase (*FLS1*) was the rate-limiting step in quercetin biosynthesis.
CRISPR knockout of FLS1 abolished flavonol accumulation completely.
"""

def test_simple(client, model_name, label):
    """测试 1：简单 schema"""
    print(f"\n{'='*60}")
    print(f"🧪 测试1 (简单): {label} ({model_name})")
    print(f"{'='*60}")

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": SIMPLE_PROMPT},
            ],
            tools=[SIMPLE_TOOL],
            tool_choice={"type": "function", "function": {"name": "test_array_of_objects"}},
            temperature=0,
            max_tokens=1024,
        )
        msg = response.choices[0].message
        if msg.tool_calls:
            args = json.loads(msg.tool_calls[0].function.arguments)
            items = args.get("items", [])
            print(f"  ✅ items 数量: {len(items)}")
            return len(items) > 0
        else:
            print(f"  ❌ 无 tool call")
            return False
    except Exception as e:
        print(f"  ❌ 异常: {e}")
        return False


def test_classify(client, model_name, label):
    """测试 2：真实 classify_genes schema"""
    print(f"\n{'='*60}")
    print(f"🧪 测试2 (classify): {label} ({model_name})")
    print(f"{'='*60}")

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a plant biology expert. Extract genes from papers using the provided tools."},
                {"role": "user", "content": (
                    "Classify all core genes from this paper's Results section.\n\n"
                    f"{PAPER_ABSTRACT}\n\n"
                    "Call classify_genes with all genes you find."
                )},
            ],
            tools=[CLASSIFY_TOOL],
            tool_choice={"type": "function", "function": {"name": "classify_genes"}},
            temperature=0,
            max_tokens=2048,
        )
        msg = response.choices[0].message
        print(f"  finish_reason: {response.choices[0].finish_reason}")

        if msg.tool_calls:
            raw = msg.tool_calls[0].function.arguments
            print(f"  raw arguments 长度: {len(raw)} 字符")
            print(f"  raw arguments 完整内容:\n{raw}")
            args = json.loads(raw)
            genes = args.get("genes", [])
            print(f"  genes 数量: {len(genes)}")
            for g in genes:
                print(f"     - Gene_Name={g.get('Gene_Name')!r}, category={g.get('category')!r}")
                print(f"       所有字段: {list(g.keys())}")
            return len(genes) > 0 and all(g.get("Gene_Name") for g in genes)
        else:
            print(f"  ❌ 无 tool call")
            if msg.content:
                print(f"  文本响应: {msg.content[:300]}")
            return False
    except Exception as e:
        print(f"  ❌ 异常: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Function Calling 测试")
    print(f"   Primary: {PRIMARY_MODEL}")
    print(f"   Fallback: {FALLBACK_MODEL or '未配置'}")

    clients = [("主 API", primary_client, PRIMARY_MODEL)]
    if fallback_client:
        clients.append(("Fallback", fallback_client, FALLBACK_MODEL))

    results = {}
    for label, c, m in clients:
        r1 = test_simple(c, m, label)
        r2 = test_classify(c, m, label)
        results[label] = {"simple": r1, "classify": r2}

    print(f"\n{'='*60}")
    print(f"📊 测试结果汇总")
    print(f"{'='*60}")
    for label, r in results.items():
        s1 = "✅" if r["simple"] else "❌"
        s2 = "✅" if r["classify"] else "❌"
        print(f"  {label}: 简单={s1}  classify_genes={s2}")
