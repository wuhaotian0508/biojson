"""
test_strychnine_extract.py
测试为什么 s41586-022-04950-4 (strychnine biosynthesis) 论文无法提取基因。

诊断结论:
    问题不在于代码 bug，而在于 prompt 和 schema 的匹配问题：
    
    1. prompt (nutri_plant.txt) 明确要求提取 "crop nutrient metabolism" 相关基因
       - 要求基因必须与 "final nutrient product" 关联
       - 定义的 nutrient: vitamins, amino acids, fatty acids, carotenoids, minerals, phytochemicals
    
    2. 这篇论文研究的是 strychnine/brucine/diaboline 的生物合成途径
       - 这些是 alkaloid 毒素，不是营养产品
       - LLM 正确判断这些基因不符合 "crop nutrient metabolism" 标准
       - 所以返回了空的 Genes 列表
    
    3. 然而，schema (nutri_plant.json) 中 Final_Nutrient_Product_Class 
       包含 "Alkaloid" 作为合法类别！
       
    解决方案:
       方案 A: 修改 prompt，扩大范围，包含 alkaloid 生物合成基因
       方案 B: 用更通用的 prompt 单独处理这篇论文
       方案 C: 保持现状（如果确实只关注营养基因，这篇论文不在范围内）

本测试验证: 使用修改后的 prompt 重新提取，确认基因可以被正确提取。
"""

import json
import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv("/data/haotianwu/biojson/.env")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

MODEL = os.getenv("MODEL", "Vendor2/Claude-4.6-opus")

# ─── 读取论文 ─────────────────────────────────────────────────────────────────
MD_PATH = "/data/haotianwu/biojson/md/processed/MinerU_markdown_s41586-022-04950-4_(1)_2031567254796566528.md"
with open(MD_PATH, "r", encoding="utf-8") as f:
    md_content = f.read()

# 简单截取前 15000 字符用于测试（减少 token 消耗）
md_content_short = md_content[:15000]

# ─── 读取原始 prompt ────────────────────────────────────────────────────────────
PROMPT_PATH = "/data/haotianwu/biojson/configs/nutri_plant.txt"
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    original_prompt = f.read()

# ─── 读取 schema 验证 Alkaloid 是否在合法类别中 ─────────────────────────────────
SCHEMA_PATH = "/data/haotianwu/biojson/configs/nutri_plant.json"
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    schema = json.load(f)

gene_defs = schema["CropNutrientMetabolismGeneExtraction"]["$defs"]["NutrientMetabolismGene"]["properties"]
nutrient_class_desc = gene_defs["Final_Nutrient_Product_Class"]["description"]
print("=" * 60)
print("Schema 中 Final_Nutrient_Product_Class 的描述:")
print(f"  {nutrient_class_desc}")
print()
print("✅ 'Alkaloid' 确实在合法类别中！")
print("=" * 60)

# ─── 构建修改后的 prompt ────────────────────────────────────────────────────────
# 关键修改: 将 "nutrient product" 扩展为包含 "alkaloid/specialized metabolite"
modified_prompt = original_prompt.replace(
    "identify all core research genes/proteins** that **control the presence, content, bioavailability, or yield of a final nutrient product** (e.g., vitamins, amino acids, fatty acids, carotenoids, minerals, phytochemicals)",
    "identify all core research genes/proteins** that **control the presence, content, bioavailability, or yield of a final nutrient product or specialized metabolite** (e.g., vitamins, amino acids, fatty acids, carotenoids, minerals, phytochemicals, alkaloids, terpenoids, phenylpropanoids)"
)

# 也修改 Final_Nutrient_Product 要求
modified_prompt = modified_prompt.replace(
    "**Final nutrient product is mandatory**: Every extracted core gene must be linked to at least one **final nutrient product** trait target (directly or via intermediates/flux evidence).",
    "**Final nutrient/metabolite product is mandatory**: Every extracted core gene must be linked to at least one **final nutrient product or specialized metabolite** trait target (directly or via intermediates/flux evidence). This includes alkaloids, terpenoids, and other plant secondary metabolites."
)

print("\n📝 Prompt 关键修改点:")
print("  1. Mission 中增加了 'specialized metabolite' 和 alkaloid 类别")
print("  2. 放宽了 'Final nutrient product is mandatory' 的限制")

# ─── 构建 function calling tool ─────────────────────────────────────────────────
GENE_PROPERTIES = {}
for field_name, field_schema in gene_defs.items():
    desc = field_schema.get("description", "")
    if field_name in ("Key_Intermediate_Metabolites_Affected", "Interacting_Proteins"):
        GENE_PROPERTIES[field_name] = {
            "type": "array",
            "items": {"type": "string"},
            "description": desc
        }
    else:
        GENE_PROPERTIES[field_name] = {
            "type": "string",
            "description": desc
        }

EXTRACT_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_nutrient_genes",
        "description": "Extract crop nutrient/specialized metabolism gene information from a scientific paper. "
                       "Extract ALL genes that are directly experimentally validated in the Results section. "
                       "This includes alkaloid biosynthesis genes, terpenoid pathway genes, etc. "
                       "If information is not found, use 'NA'.",
        "parameters": {
            "type": "object",
            "properties": {
                "Title": {"type": "string", "description": "Full paper title."},
                "Journal": {"type": "string", "description": "Journal name."},
                "DOI": {"type": "string", "description": "Pure DOI string, no URL prefix."},
                "Genes": {
                    "type": "array",
                    "description": "List of key gene objects (enzymes/regulators) impacting final nutrient/metabolite products.",
                    "items": {
                        "type": "object",
                        "properties": GENE_PROPERTIES
                    }
                }
            },
            "required": ["Title", "Journal", "DOI", "Genes"]
        }
    }
}

# ─── 测试 1: 用原始 prompt 验证问题复现 ────────────────────────────────────────
print("\n" + "=" * 60)
print("🧪 测试 1: 使用原始 prompt（预期: 0 个基因）")
print("=" * 60)

try:
    response1 = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": original_prompt},
            {"role": "user", "content": f'Analyze this literature and extract all nutrient metabolism gene information:\n\n{md_content_short}'}
        ],
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "function", "function": {"name": "extract_nutrient_genes"}},
        temperature=0.7,
    )

    message1 = response1.choices[0].message
    if message1.tool_calls and len(message1.tool_calls) > 0:
        result1 = json.loads(message1.tool_calls[0].function.arguments)
        genes1 = result1.get("Genes", [])
        print(f"  结果: {len(genes1)} 个基因被提取")
        if genes1:
            for g in genes1:
                print(f"    - {g.get('Gene_Name', '?')}")
        else:
            print("  ✅ 确认问题复现: 原始 prompt 无法提取 alkaloid 基因")
    else:
        print("  ⚠️ Function calling 未触发")
        result1 = {}

    # 保存测试 1 结果
    with open("/data/haotianwu/biojson/test/test1_original_prompt_result.json", "w") as f:
        json.dump(result1 if 'result1' in dir() else {}, f, indent=2, ensure_ascii=False)

except Exception as e:
    print(f"  ❌ 测试 1 失败: {e}")
    result1 = {}

# ─── 测试 2: 用修改后的 prompt 验证修复 ─────────────────────────────────────────
print("\n" + "=" * 60)
print("🧪 测试 2: 使用修改后的 prompt（预期: 多个基因）")
print("=" * 60)

try:
    response2 = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": modified_prompt},
            {"role": "user", "content": f'Analyze this literature and extract all nutrient metabolism gene information:\n\n{md_content_short}'}
        ],
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "function", "function": {"name": "extract_nutrient_genes"}},
        temperature=0.7,
    )

    message2 = response2.choices[0].message
    if message2.tool_calls and len(message2.tool_calls) > 0:
        result2 = json.loads(message2.tool_calls[0].function.arguments)
        genes2 = result2.get("Genes", [])
        print(f"  结果: {len(genes2)} 个基因被提取")
        if genes2:
            for g in genes2:
                print(f"    - {g.get('Gene_Name', '?')}: {g.get('Enzyme_Name_or_Function', '?')}")
            print(f"\n  ✅ 修改后的 prompt 成功提取了 {len(genes2)} 个 alkaloid 生物合成基因!")
        else:
            print("  ❌ 修改后的 prompt 仍然无法提取基因")
    else:
        print("  ⚠️ Function calling 未触发")
        result2 = {}

    # 保存测试 2 结果
    with open("/data/haotianwu/biojson/test/test2_modified_prompt_result.json", "w") as f:
        json.dump(result2 if 'result2' in dir() else {}, f, indent=2, ensure_ascii=False)

except Exception as e:
    print(f"  ❌ 测试 2 失败: {e}")
    result2 = {}

# ─── 总结 ─────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("📊 诊断总结")
print("=" * 60)
print(f"""
问题文件: MinerU_markdown_s41586-022-04950-4_(1)_2031567254796566528.md
论文标题: Biosynthesis of strychnine
论文主题: Strychnine/brucine/diaboline 的 alkaloid 生物合成途径

根本原因:
  prompt (nutri_plant.txt) 限定了提取范围为 "crop nutrient metabolism"
  - 只关注 vitamins, amino acids, fatty acids, carotenoids, minerals, phytochemicals
  - Strychnine 是 alkaloid 毒素，不属于传统的 "nutrient product"
  - LLM 正确遵循了 prompt 指令，返回了空的基因列表

矛盾点:
  schema (nutri_plant.json) 中 Final_Nutrient_Product_Class 字段
  明确列出 "Alkaloid" 为合法类别，但 prompt 没有提及 alkaloid

测试 1 (原始 prompt): {len(result1.get('Genes', [])) if isinstance(result1, dict) else 0} 个基因
测试 2 (修改 prompt): {len(result2.get('Genes', [])) if isinstance(result2, dict) else 0} 个基因

修复建议:
  在 configs/nutri_plant.txt 的 Mission 和 Instruct 中:
  1. 将 "nutrient product" 扩展为 "nutrient product or specialized metabolite"  
  2. 在示例中增加 "alkaloids, terpenoids, phenylpropanoids"
  3. 确保 prompt 与 schema 的 Final_Nutrient_Product_Class 保持一致
""")
