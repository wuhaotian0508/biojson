"""
test_strychnine_full.py
最终验证: 使用修改后的 prompt + 完整论文文本，提取 strychnine 论文中的基因。

问题根因已确认:
  1. 原始 prompt (nutri_plant.txt) 限定了 "crop nutrient metabolism"，排斥了 alkaloid 类论文
  2. schema 中 Final_Nutrient_Product_Class 包含 "Alkaloid"，但 prompt 没有提及
  3. 简化 prompt 已证明 API/模型完全可以提取这些基因

本测试: 使用修改后的 nutri_plant prompt（增加 alkaloid/specialized metabolite 覆盖）
发送完整论文进行提取验证。
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

# ─── 读取并预处理论文 ──────────────────────────────────────────────────────────
MD_PATH = "/data/haotianwu/biojson/md/processed/MinerU_markdown_s41586-022-04950-4_(1)_2031567254796566528.md"
with open(MD_PATH, "r", encoding="utf-8") as f:
    md_content = f.read()

original_len = len(md_content)
md_content = strip_references(md_content)
print(f"📏 文本预处理: {original_len:,} → {len(md_content):,} 字符")

# ─── 读取原始 prompt 并修改 ────────────────────────────────────────────────────
PROMPT_PATH = "/data/haotianwu/biojson/configs/nutri_plant.txt"
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    prompt = f.read()

# 修改 1: Mission 中扩展范围
prompt = prompt.replace(
    "identify all core research genes/proteins** that **control the presence, content, bioavailability, or yield of a final nutrient product** (e.g., vitamins, amino acids, fatty acids, carotenoids, minerals, phytochemicals)",
    "identify all core research genes/proteins** that **control the presence, content, bioavailability, or yield of a final nutrient product or specialized metabolite** (e.g., vitamins, amino acids, fatty acids, carotenoids, minerals, phytochemicals, alkaloids, terpenoids, phenylpropanoids, and other plant secondary metabolites)"
)

# 修改 2: Step 1 中扩展 nutrient-trait target 定义
prompt = prompt.replace(
    "What is the paper's **final nutrient product(s)** being measured or engineered?\n\n     * Examples: provitamin A (β-carotene), vitamin E (tocopherols), folate, lysine, methionine, omega-3 fatty acids, anthocyanins, iron/zinc accumulation, etc.",
    "What is the paper's **final nutrient product(s) or specialized metabolite(s)** being measured or engineered?\n\n     * Examples: provitamin A (β-carotene), vitamin E (tocopherols), folate, lysine, methionine, omega-3 fatty acids, anthocyanins, iron/zinc accumulation, strychnine, alkaloids, terpenoids, glucosinolates, etc."
)

# 修改 3: Step 2 中放宽 Final nutrient product 要求
prompt = prompt.replace(
    "**Final nutrient product is mandatory**: Every extracted core gene must be linked to at least one **final nutrient product** trait target (directly or via intermediates/flux evidence).",
    "**Final nutrient/metabolite product is mandatory**: Every extracted core gene must be linked to at least one **final nutrient product or specialized metabolite** trait target (directly or via intermediates/flux evidence). This includes alkaloids, terpenoids, and other plant secondary metabolites."
)

# 修改 4: Step 3 Trait validity 扩展
prompt = prompt.replace(
    '2. **Trait validity**: Is the gene linked to a **final nutrient product** (not only a generic "growth" trait)?',
    '2. **Trait validity**: Is the gene linked to a **final nutrient product or specialized metabolite** (not only a generic "growth" trait)?'
)

print("✅ Prompt 已修改（4 处关键改动）")

# ─── 构建 function calling tool ─────────────────────────────────────────────────
SCHEMA_PATH = "/data/haotianwu/biojson/configs/nutri_plant.json"
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    schema = json.load(f)

gene_defs = schema["CropNutrientMetabolismGeneExtraction"]["$defs"]["NutrientMetabolismGene"]["properties"]

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

# ─── 调用 API ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("🧪 使用修改后的 prompt + 完整论文提取基因")
print("=" * 60)

try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f'Analyze this literature and extract all nutrient metabolism gene information:\n\n{md_content}'}
        ],
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "function", "function": {"name": "extract_nutrient_genes"}},
        temperature=0.7,
    )

    message = response.choices[0].message
    print(f"\nfinish_reason: {response.choices[0].finish_reason}")
    
    if message.tool_calls and len(message.tool_calls) > 0:
        tool_call = message.tool_calls[0]
        result = json.loads(tool_call.function.arguments)
        genes = result.get("Genes", [])
        
        # 防御：Genes 可能被序列化为字符串
        if isinstance(genes, str):
            genes = json.loads(genes)
            result["Genes"] = genes
        
        print(f"\n✅ Function calling 成功! 提取到 {len(genes)} 个基因:")
        for i, g in enumerate(genes, 1):
            name = g.get("Gene_Name", "?")
            func = g.get("Enzyme_Name_or_Function", "?")
            accession = g.get("Gene_Accession_Number", "?")
            species = g.get("Species_Latin_Name", g.get("Species", "?"))
            product = g.get("Final_Nutrient_Product", "?")
            print(f"  [{i}] {name}")
            print(f"      Function: {func}")
            print(f"      Accession: {accession}")
            print(f"      Species: {species}")
            print(f"      Product: {product}")
            print()
        
        # 保存结果
        output_path = "/data/haotianwu/biojson/test/test_full_extraction_result.json"
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"📄 结果已保存: {output_path}")
        
        # 验证: 检查论文中已知的基因是否都被提取到了
        expected_genes = [
            "SnvGO", "SnvNS1", "SnvNS2", "SnvNO", "SnvWS", "SnvAT",
            "Snv10H", "SnvOMT", "Snv11H",
            "SpGO", "SpNS1", "SpNS2", "SpNO", "SpWS", "SpAT"
        ]
        extracted_names = [g.get("Gene_Name", "") for g in genes]
        extracted_names_str = " ".join(extracted_names)
        
        print("\n📊 基因覆盖率验证:")
        found = 0
        for eg in expected_genes:
            if eg in extracted_names_str:
                print(f"  ✅ {eg}")
                found += 1
            else:
                print(f"  ❌ {eg} (未找到)")
        print(f"\n  覆盖率: {found}/{len(expected_genes)} ({found/len(expected_genes)*100:.0f}%)")
        
    else:
        print("\n⚠️ Function calling 未触发!")
        if message.content:
            print(f"Content: {message.content[:2000]}")
            
            # Fallback: 从 content 提取
            code_match = re.search(r'```json\s*(.*?)\s*```', message.content, re.DOTALL)
            if code_match:
                fallback = json.loads(code_match.group(1))
                genes = fallback.get("Genes", [])
                print(f"\n📦 Fallback 提取到 {len(genes)} 个基因")
                
                output_path = "/data/haotianwu/biojson/test/test_full_extraction_result.json"
                with open(output_path, "w") as f:
                    json.dump(fallback, f, indent=2, ensure_ascii=False)

except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()
