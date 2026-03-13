import re
import json
import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from token_tracker import TokenTracker
load_dotenv()

# 1. 初始化客户端
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")  # 确保加上了 /v1
)

# Token 用量追踪
tracker = TokenTracker(model=os.getenv("MODEL", "Vendor2/Claude-4.6-opus"))

# 2. 路径配置 (从环境变量读取，run.sh 统一管理)
BASE_DIR = os.getenv("BASE_DIR", "/data/haotianwu/biojson")
INPUT_DIR = os.getenv("MD_DIR", os.path.join(BASE_DIR, "md"))
OUTPUT_DIR = os.getenv("JSON_DIR", os.path.join(BASE_DIR, "json"))
PROMPT_PATH = os.getenv("PROMPT_PATH", os.path.join(BASE_DIR, "configs/nutri_plant.txt"))
SCHEMA_PATH = os.getenv("SCHEMA_PATH", os.path.join(BASE_DIR, "configs/nutri_plant.json"))
REPORT_DIR = os.getenv("REPORT_DIR", os.path.join(BASE_DIR, "reports"))

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# 3. 读取 Prompt 和 Schema
with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
    base_prompt = f.read()

with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
    template = json.load(f)
    # 假设你的 schema 在这个 key 下
    paradigm = template.get("CropNutrientMetabolismGeneExtraction", template)

# 4. 核心提取逻辑
def ai_response(path):
    name = os.path.basename(path)
    filename = os.path.splitext(name)[0]
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 增强提示词约束：强制要求不输出解释和思考过程
    strict_constraint = (
        "\n\n### STRICT OUTPUT RULES:\n"
        "1. YOU MUST ONLY output the JSON object.\n"
        "2. DO NOT include any thinking process, <thinking> tags, or introductory text.\n"
        "3. WRAP the JSON strictly inside <structured_information> tags.\n"
        "4. If information is missing, use \"NA\"."
    )

    try:
        response = client.chat.completions.create(
            model=os.getenv("MODEL", "Vendor2/Claude-4.6-opus"),
            messages=[
                {"role": "system", "content": base_prompt + strict_constraint},
                {"role": "system", "content": f'JSON Schema:\n```json\n{json.dumps(paradigm, indent=2, ensure_ascii=False)}\n```'},
                {"role": "user", "content": f'Analyze this literature and fill the JSON schema strictly:\n\n{content}'}
            ],
            temperature=float(os.getenv("TEMPERATURE", "0")),
            max_tokens=int(os.getenv("MAX_TOKENS", "18192")),
        )
        
        # 记录 Token 用量
        tracker.add(response, stage="extract", file=name)
        
        raw_result = response.choices[0].message.content
        
        # --- 多重正则提取逻辑 ---
        # 优先提取 <structured_information> 标签内的内容
        tag_match = re.search(r'<structured_information>(.*?)</structured_information>', raw_result, re.DOTALL)
        
        if tag_match:
            clean_json = tag_match.group(1).strip()
        else:
            # 备选 1：尝试匹配 Markdown 代码块
            code_match = re.search(r'```json\s*(.*?)\s*```', raw_result, re.DOTALL)
            if code_match:
                clean_json = code_match.group(1).strip()
            else:
                # 备选 2：强力提取第一个 { 到最后一个 } 之间的内容
                brace_match = re.search(r'(\{.*\})', raw_result, re.DOTALL)
                clean_json = brace_match.group(1).strip() if brace_match else raw_result

        # --- JSON 校验 ---
        try:
            json_data = json.loads(clean_json)
            final_output = json.dumps(json_data, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            print(f"Error: {name} 的输出不是合法 JSON，将保存原始清洗结果。")
            final_output = clean_json

        # 5. 保存结果
        output_path = os.path.join(OUTPUT_DIR, f'{filename}_nutri_plant.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_output)
        
        print(f"成功处理: {name} -> {output_path}")

    except Exception as e:
        print(f"处理文件 {name} 时发生错误: {str(e)}")

# 6. 遍历执行
if __name__ == "__main__":
    if not os.path.exists(INPUT_DIR):
        print(f"错误: 输入目录 {INPUT_DIR} 不存在！")
    else:
        files = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith('.md')])
        print(f"找到 {len(files)} 个待处理文件...")

        # 测试模式：仅处理指定编号的文件
        if os.getenv("TEST_MODE") == "1":
            idx = int(os.getenv("TEST_INDEX", "1")) - 1  # 转为 0-based
            if 0 <= idx < len(files):
                files = [files[idx]]
                print(f"🧪 测试模式: 仅处理第 {idx + 1} 个文件 → {files[0]}")
            else:
                print(f"❌ 编号 {idx + 1} 超出范围 (共 {len(files)} 个文件)")
                files = []

        for file in files:
            ai_response(os.path.join(INPUT_DIR, file))

        # 打印 Token 用量汇总并保存报告
        tracker.print_summary()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tracker.save_report(os.path.join(REPORT_DIR, f"token_usage_extract_{timestamp}.json"))
