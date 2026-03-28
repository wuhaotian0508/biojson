"""
test_strychnine_refusal.py
调查 finish_reason: refusal 的问题

关键发现: 当发送完整论文文本 + 修改后的 prompt 时，模型返回 refusal。
可能原因:
  1. Strychnine 是一种神经毒素/杀鼠剂，模型安全过滤器可能拒绝处理
  2. 论文文本太长，超出了 token 限制导致截断
  3. prompt 太长 + 论文太长导致请求被拒绝

测试策略:
  A. 检查 refusal 的具体内容
  B. 发送不同长度的文本，找到 refusal 的边界
  C. 尝试去除敏感词（如 "pesticide", "neurotoxicity" 等）
"""

import json
import os
import re
import sys
sys.path.insert(0, "/data/haotianwu/biojson/scripts")
from openai import OpenAI
from dotenv import load_dotenv
from text_utils import strip_references

load_dotenv("/data/haotianwu/biojson/.env")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

MODEL = os.getenv("MODEL", "Vendor2/Claude-4.6-opus")

# 读取论文
MD_PATH = "/data/haotianwu/biojson/md/processed/MinerU_markdown_s41586-022-04950-4_(1)_2031567254796566528.md"
with open(MD_PATH, "r", encoding="utf-8") as f:
    md_content = f.read()

md_content = strip_references(md_content)

# 读取原始 prompt
PROMPT_PATH = "/data/haotianwu/biojson/configs/nutri_plant.txt"
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    original_prompt = f.read()

# 简单 tool
SIMPLE_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_genes",
        "description": "Extract gene information from a scientific paper.",
        "parameters": {
            "type": "object",
            "properties": {
                "Title": {"type": "string"},
                "Genes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "Gene_Name": {"type": "string"},
                            "Function": {"type": "string"},
                            "Species": {"type": "string"},
                            "Accession": {"type": "string"}
                        }
                    }
                }
            },
            "required": ["Title", "Genes"]
        }
    }
}

simple_system = """You are an expert in plant molecular biology and biochemistry.
Your task is to extract all experimentally characterized genes from scientific literature about plant biosynthetic pathways.
Extract gene names, functions, species, and accession numbers."""


def test_extraction(label, text, system_prompt):
    """测试提取，返回详细信息"""
    print(f"\n{'─'*60}")
    print(f"🧪 {label}")
    print(f"   文本长度: {len(text):,} 字符")
    print(f"{'─'*60}")
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f'Extract all experimentally validated genes:\n\n{text}'}
            ],
            tools=[SIMPLE_TOOL],
            tool_choice={"type": "function", "function": {"name": "extract_genes"}},
            temperature=0.7,
        )
        
        msg = response.choices[0].message
        fr = response.choices[0].finish_reason
        
        print(f"  finish_reason: {fr}")
        
        if fr == "refusal":
            refusal_text = getattr(msg, 'refusal', None) or msg.content or "无 refusal 信息"
            print(f"  ❌ REFUSAL: {refusal_text[:500]}")
            return 0
        
        if msg.tool_calls and len(msg.tool_calls) > 0:
            result = json.loads(msg.tool_calls[0].function.arguments)
            genes = result.get("Genes", [])
            print(f"  ✅ 提取到 {len(genes)} 个基因:")
            for g in genes:
                print(f"    - {g.get('Gene_Name', '?')}: {g.get('Function', '?')[:60]}")
            return len(genes)
        else:
            print(f"  ⚠️ 未触发 tool_calls")
            if msg.content:
                print(f"  Content: {msg.content[:300]}")
            return 0
            
    except Exception as e:
        print(f"  ❌ 异常: {e}")
        return 0


# ═══════════════════════════════════════════════════════════
# 测试 A: 不同文本长度
# ═══════════════════════════════════════════════════════════
print("=" * 60)
print("📊 测试 A: 不同文本长度 (使用简单 prompt)")
print("=" * 60)

results = {}
for length in [8000, 15000, 25000, 40000, len(md_content)]:
    text = md_content[:length]
    n = test_extraction(f"文本长度 {length:,} 字符", text, simple_system)
    results[length] = n

print("\n\n" + "=" * 60)
print("📊 测试 A 汇总:")
for length, n_genes in results.items():
    status = "✅" if n_genes > 0 else "❌"
    print(f"  {status} {length:>6,} 字符 → {n_genes} 个基因")
print("=" * 60)

# ═══════════════════════════════════════════════════════════
# 测试 B: 使用原始 prompt + 不同长度
# ═══════════════════════════════════════════════════════════
print("\n\n" + "=" * 60)
print("📊 测试 B: 原始 nutri_plant prompt + 不同长度")
print("=" * 60)

# 只测试一个关键长度
n = test_extraction("原始prompt + 15000字符", md_content[:15000], original_prompt)
print(f"\n  原始 prompt 结果: {n} 个基因")

print("\n\n" + "=" * 60)
print("📊 最终结论")
print("=" * 60)
