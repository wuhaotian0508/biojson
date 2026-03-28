"""
test_strychnine_debug.py
深入调试: 查看 API 实际返回了什么内容
"""

import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv("/data/haotianwu/biojson/.env")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

MODEL = os.getenv("MODEL", "Vendor2/Claude-4.6-opus")

# ─── 读取论文（截取前 8000 字符减少 token）─────────────────────────────────────
MD_PATH = "/data/haotianwu/biojson/md/processed/MinerU_markdown_s41586-022-04950-4_(1)_2031567254796566528.md"
with open(MD_PATH, "r", encoding="utf-8") as f:
    md_content = f.read()[:8000]

# ─── 用一个非常简单直接的 prompt 测试 ───────────────────────────────────────────
simple_prompt = """You are an expert in plant molecular biology. 
Extract ALL genes/enzymes that are experimentally characterized in this paper.
For each gene, extract: Gene_Name, Species, Enzyme_Name_or_Function, Gene_Accession_Number.
Include alkaloid biosynthesis genes, specialized metabolite genes, etc.
Call the extract_genes function with your results."""

SIMPLE_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_genes",
        "description": "Extract gene information from a scientific paper. Extract ALL experimentally validated genes.",
        "parameters": {
            "type": "object",
            "properties": {
                "Title": {"type": "string", "description": "Paper title"},
                "Genes": {
                    "type": "array",
                    "description": "List of genes",
                    "items": {
                        "type": "object",
                        "properties": {
                            "Gene_Name": {"type": "string", "description": "Gene symbol/name"},
                            "Species": {"type": "string", "description": "Species"},
                            "Enzyme_Name_or_Function": {"type": "string", "description": "Function"},
                            "Gene_Accession_Number": {"type": "string", "description": "Accession number"},
                            "Final_Product": {"type": "string", "description": "Final metabolite product"}
                        }
                    }
                }
            },
            "required": ["Title", "Genes"]
        }
    }
}

print("=" * 60)
print("🧪 调试测试: 简化 prompt + 简化 schema")
print(f"   模型: {MODEL}")
print(f"   文本长度: {len(md_content)} 字符")
print("=" * 60)

try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": simple_prompt},
            {"role": "user", "content": f'Extract all genes from this paper:\n\n{md_content}'}
        ],
        tools=[SIMPLE_TOOL],
        tool_choice={"type": "function", "function": {"name": "extract_genes"}},
        temperature=0.7,
    )

    message = response.choices[0].message
    
    print(f"\n📋 API 返回信息:")
    print(f"  finish_reason: {response.choices[0].finish_reason}")
    print(f"  message.role: {message.role}")
    print(f"  message.content: {repr(message.content[:500]) if message.content else 'None'}")
    print(f"  message.tool_calls: {message.tool_calls}")
    
    if message.tool_calls and len(message.tool_calls) > 0:
        tool_call = message.tool_calls[0]
        print(f"\n✅ Function calling 触发了!")
        print(f"  function name: {tool_call.function.name}")
        args = json.loads(tool_call.function.arguments)
        genes = args.get("Genes", [])
        print(f"  提取到 {len(genes)} 个基因:")
        for g in genes:
            print(f"    - {g.get('Gene_Name', '?')}: {g.get('Enzyme_Name_or_Function', '?')} ({g.get('Gene_Accession_Number', '?')})")
        
        with open("/data/haotianwu/biojson/test/debug_result.json", "w") as f:
            json.dump(args, f, indent=2, ensure_ascii=False)
    else:
        print(f"\n⚠️ Function calling 未触发!")
        print(f"  完整 content:")
        if message.content:
            print(f"  {message.content[:2000]}")
        
        # 尝试从 content 中提取 JSON
        if message.content:
            import re
            json_match = re.search(r'\{.*\}', message.content, re.DOTALL)
            if json_match:
                try:
                    fallback_data = json.loads(json_match.group())
                    print(f"\n  📦 从 content 中提取到 JSON:")
                    genes = fallback_data.get("Genes", [])
                    print(f"    {len(genes)} 个基因")
                    for g in genes:
                        print(f"      - {g.get('Gene_Name', '?')}")
                except:
                    print("  ❌ 无法解析 JSON")

except Exception as e:
    print(f"❌ API 调用失败: {e}")
    import traceback
    traceback.print_exc()

# ─── 测试 2: 不使用 function calling，直接让 LLM 返回 JSON ──────────────────────
print("\n\n" + "=" * 60)
print("🧪 测试 2: 不使用 function calling，直接让 LLM 输出 JSON")
print("=" * 60)

try:
    response2 = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a plant biology expert. Extract gene information and return as JSON."},
            {"role": "user", "content": f"""Extract ALL experimentally characterized genes from this paper. 
Return a JSON object with this format:
{{
  "Title": "paper title",
  "Genes": [
    {{
      "Gene_Name": "...",
      "Gene_Accession_Number": "...",  
      "Species": "...",
      "Enzyme_Name_or_Function": "...",
      "Final_Product": "..."
    }}
  ]
}}

Paper:
{md_content[:6000]}"""}
        ],
        temperature=0.7,
    )

    content2 = response2.choices[0].message.content
    print(f"\n📋 返回内容 (前 3000 字符):")
    print(content2[:3000] if content2 else "None")
    
    # 尝试提取 JSON
    if content2:
        import re
        # 尝试提取 JSON 代码块
        code_match = re.search(r'```json\s*(.*?)\s*```', content2, re.DOTALL)
        if code_match:
            json_str = code_match.group(1)
        else:
            json_match = re.search(r'\{.*\}', content2, re.DOTALL)
            json_str = json_match.group() if json_match else None
        
        if json_str:
            data2 = json.loads(json_str)
            genes2 = data2.get("Genes", [])
            print(f"\n✅ 成功提取 {len(genes2)} 个基因:")
            for g in genes2:
                print(f"  - {g.get('Gene_Name', '?')}: {g.get('Enzyme_Name_or_Function', '?')} | Accession: {g.get('Gene_Accession_Number', '?')}")
            
            with open("/data/haotianwu/biojson/test/debug_result_no_fc.json", "w") as f:
                json.dump(data2, f, indent=2, ensure_ascii=False)

except Exception as e:
    print(f"❌ 测试 2 失败: {e}")
    import traceback
    traceback.print_exc()
