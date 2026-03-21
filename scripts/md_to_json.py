"""
md_to_json.py  (v4 — 硬编码 2 步 API 调用)

提取模块：通过 load_skill() 从 SKILL.md 加载 tools，
代码硬编码调用顺序：
  API Call #1: classify_genes  → 得到 gene_dict
  API Call #2: extract_*_genes → 得到详细字段

对外暴露:
    extract_paper(md_path, registry=None) -> (extraction_dict, gene_dict)
    供 pipeline.py 调用。

也可独立运行:
    python scripts/md_to_json.py
"""

import json
import os
import sys
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from token_tracker import TokenTracker
from text_utils import preprocess_md
from tool_registry import load_skill, load_skill_list

load_dotenv()

# ─── 客户端初始化 ────────────────────────────────────────────────────────────────
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

fallback_client = None
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "")
if os.getenv("FALLBACK_API_KEY") and os.getenv("FALLBACK_BASE_URL"):
    fallback_client = OpenAI(
        api_key=os.getenv("FALLBACK_API_KEY"),
        base_url=os.getenv("FALLBACK_BASE_URL"),
    )
    print(f"🔄 Fallback 已配置: {FALLBACK_MODEL}")

tracker = TokenTracker(model=os.getenv("MODEL", "Vendor2/Claude-4.6-opus"))

# ─── 路径配置 ─────────────────────────────────────────────────────────────────────
BASE_DIR = os.getenv("BASE_DIR", "/data/haotianwu/biojson")
INPUT_DIR = os.getenv("MD_DIR", os.path.join(BASE_DIR, "md"))
REPORTS_DIR = os.getenv("REPORTS_DIR", os.path.join(BASE_DIR, "reports"))
PROMPT_PATH = os.getenv("PROMPT_PATH", os.path.join(BASE_DIR, "configs/nutri_gene_prompt_v2.txt"))
TOKEN_USAGE_DIR = os.getenv("TOKEN_USAGE_DIR", os.path.join(BASE_DIR, "token-usage"))
SKILLS_DIR = os.path.join(BASE_DIR, "skills")
EXTRACTION_SKILL_DIR = os.path.join(SKILLS_DIR, "biojson-extraction")

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(TOKEN_USAGE_DIR, exist_ok=True)


def stem_to_dirname(stem):
    """将 MD 文件名 stem 转为 reports 子目录名（GitHub 命名规范）。"""
    if stem.startswith("MinerU_markdown_"):
        stem = stem[len("MinerU_markdown_"):]
    stem = stem.replace("_(1)", "")
    stem = stem.replace("_", "-")
    return stem


# ─── 读取 Prompt ─────────────────────────────────────────────────────────────────
with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
    base_prompt = f.read()


# ─── 启动时打印技能列表 ──────────────────────────────────────────────────────────
def _print_skill_list():
    """扫描并打印所有可用技能。"""
    skills = load_skill_list(SKILLS_DIR)
    if skills:
        print(f"📦 发现 {len(skills)} 个技能:")
        for s in skills:
            print(f"   - {s['name']} v{s.get('version', '?')}: {s.get('description', '')[:60]}...")
            tools = s.get("tools", [])
            if tools:
                print(f"     tools: {', '.join(t['name'] for t in tools)}")
    else:
        print("⚠️  未发现任何技能")

_print_skill_list()


# ─── 加载提取技能（只取提取相关的 4 个 tools） ────────────────────────────────────
def _load_extraction_registry():
    """从 SKILL.md 加载技能，只保留提取阶段的 4 个 tools。"""
    full_registry = load_skill(EXTRACTION_SKILL_DIR, schema_base_dir=BASE_DIR)

    # 过滤：只保留提取相关的 tools（排除 verify_all_genes）
    EXTRACT_TOOL_NAMES = {"classify_genes", "extract_common_genes", "extract_pathway_genes", "extract_regulation_genes"}

    from tool_registry import ToolRegistry
    extract_registry = ToolRegistry()
    for name, tool_info in full_registry._tools.items():
        if name in EXTRACT_TOOL_NAMES:
            extract_registry.register(name, tool_info["schema"], tool_info["handler"])

    return extract_registry


# ═══════════════════════════════════════════════════════════════════════════════════
#  核心提取逻辑：硬编码 2 步 API 调用
# ═══════════════════════════════════════════════════════════════════════════════════

# 分类名 → extract tool 名的映射
CAT_TO_TOOL = {
    "Common":     "extract_common_genes",
    "Pathway":    "extract_pathway_genes",
    "Regulation": "extract_regulation_genes",
}

failed_files = []


def _call_extract_api(api_client, model, content, name, registry,
                      classify_client=None, classify_model=None):
    """硬编码 2 步 API 调用进行基因提取。

    API Call #1: classify_genes  → 得到 gene_dict
    API Call #2: extract_*_genes → 得到详细字段（根据 classify 结果决定调哪些）

    Args:
        api_client: extract 阶段使用的 API 客户端
        model: extract 阶段使用的模型
        content: 论文文本
        name: 文件名（用于 tracker）
        registry: ToolRegistry 实例
        classify_client: classify 阶段使用的 API 客户端（默认同 api_client）
        classify_model: classify 阶段使用的模型（默认同 model）

    返回 (extraction_dict, gene_dict, success)。
    """
    api_kwargs = dict(
        temperature=float(os.getenv("TEMPERATURE", "0.7")),
        max_tokens=16384,
    )

    # classify 默认用主 API
    if classify_client is None:
        classify_client = api_client
    if classify_model is None:
        classify_model = model

    # ── 构建初始 messages（两步共用同一对话历史） ──
    messages = [
        {"role": "system", "content": base_prompt},
        {"role": "user", "content": (
            "Analyze this literature and extract all nutrient metabolism gene information.\n\n"
            "Step 1: First classify all core genes from the Results section.\n"
            "Step 2: Then extract detailed fields for each gene category.\n\n"
            f"Paper content:\n\n{content}"
        )}
    ]

    # ══════════════════════════════════════════════════════════════════════════
    #  API Call #1: classify_genes（强制调用，优先用主 API）
    # ══════════════════════════════════════════════════════════════════════════
    print(f"    🔵 API Call #1: classify_genes (主 API: {classify_model})...")
    classify_args, success = registry.call_tool(
        client=classify_client,
        model=classify_model,
        messages=messages,
        tool_name="classify_genes",
        tracker=tracker,
        stage="extract",
        file_name=name,
        **api_kwargs,
    )

    # classify 失败时走 fallback
    if (not success or classify_args is None) and fallback_client and classify_client is not fallback_client:
        print(f"    🔄 classify 失败，切换到 Fallback ({FALLBACK_MODEL})...")
        # 重建 messages（classify 的 fallback 重新开始）
        messages = [
            {"role": "system", "content": base_prompt},
            {"role": "user", "content": (
                "Analyze this literature and extract all nutrient metabolism gene information.\n\n"
                "Step 1: First classify all core genes from the Results section.\n"
                "Step 2: Then extract detailed fields for each gene category.\n\n"
                f"Paper content:\n\n{content}"
            )}
        ]
        classify_args, success = registry.call_tool(
            client=fallback_client,
            model=FALLBACK_MODEL,
            messages=messages,
            tool_name="classify_genes",
            tracker=tracker,
            stage="extract",
            file_name=name,
            **api_kwargs,
        )

    if not success or classify_args is None:
        print(f"    ❌ classify_genes 全部失败")
        return None, None, False

    gene_dict = registry.state.get("gene_dict", {})
    print(f"    📋 分类结果: {len(gene_dict)} 个基因 — {gene_dict}")

    if not gene_dict:
        print(f"    ⚠️  [{model}] classify 返回空基因列表")
        return registry.state.get("extraction", {}), {}, False

    # ══════════════════════════════════════════════════════════════════════════
    #  API Call #2: extract_*_genes（根据分类硬编码决定调哪些）
    # ══════════════════════════════════════════════════════════════════════════
    needed_categories = set(gene_dict.values())
    extract_tools = []
    for cat in needed_categories:
        tool_name = CAT_TO_TOOL.get(cat)
        if tool_name:
            extract_tools.append(tool_name)

    if not extract_tools:
        print(f"    ⚠️  没有需要调用的 extract tools")
        return registry.state.get("extraction", {}), gene_dict, False

    print(f"    🔵 API Call #2: {', '.join(extract_tools)}...")

    # 在 messages 中追加一条引导消息，告诉 LLM 现在需要提取详细字段
    category_gene_map = {}
    for gname, cat in gene_dict.items():
        category_gene_map.setdefault(cat, []).append(gname)

    guide_parts = ["Now extract detailed field information for each gene category:"]
    for cat, genes in category_gene_map.items():
        guide_parts.append(f"- {cat}: {', '.join(genes)}")
    guide_parts.append("\nCall the appropriate extract_*_genes tools with all required fields.")

    messages.append({"role": "user", "content": "\n".join(guide_parts)})

    results, success = registry.call_tools(
        client=api_client,
        model=model,
        messages=messages,
        tool_names=extract_tools,
        tracker=tracker,
        stage="extract",
        file_name=name,
        **api_kwargs,
    )

    if not success:
        print(f"    ⚠️  [{model}] extract tools 调用失败")
        return registry.state.get("extraction", {}), gene_dict, False

    extraction = registry.state.get("extraction", {})

    # 统计
    c = len(extraction.get("Common_Genes", []))
    p = len(extraction.get("Pathway_Genes", []))
    r = len(extraction.get("Regulation_Genes", []))
    total = c + p + r

    tools_called = [tc.tool_name for tc in registry.call_log]
    print(f"    📊 Tool calls: {' → '.join(tools_called)}")
    print(f"    📊 基因提取: Common={c}, Pathway={p}, Regulation={r}, 总计={total}")

    if total == 0:
        print(f"    ⚠️  [{model}] 提取结果中所有基因数组均为空")
        return extraction, gene_dict, False

    return extraction, gene_dict, True


def extract_paper(md_path, registry=None):
    """提取单篇论文的基因信息。

    Args:
        md_path: MD 文件路径
        registry: 可选的 ToolRegistry 实例（不传则自动加载）

    Returns:
        (extraction_dict, gene_dict) 或 (None, None) 如果失败
    """
    name = os.path.basename(md_path)
    filename = os.path.splitext(name)[0]

    # 增量处理
    paper_dir = os.path.join(REPORTS_DIR, stem_to_dirname(filename))
    output_path = os.path.join(paper_dir, "extraction.json")
    if os.path.exists(output_path) and os.getenv("FORCE_RERUN") != "1":
        print(f"  ⏭️  已存在，跳过: {output_path}  (设置 FORCE_RERUN=1 强制重跑)")
        with open(output_path, 'r', encoding='utf-8') as f:
            extraction = json.load(f)
        gene_dict_path = os.path.join(paper_dir, "gene_dict.json")
        gene_dict = {}
        if os.path.exists(gene_dict_path):
            with open(gene_dict_path, 'r', encoding='utf-8') as f:
                gene_dict = json.load(f)
        else:
            for arr_key, cat in [("Common_Genes", "Common"), ("Pathway_Genes", "Pathway"), ("Regulation_Genes", "Regulation")]:
                for g in extraction.get(arr_key, []):
                    if isinstance(g, dict):
                        gname = g.get("Gene_Name", "")
                        if gname:
                            gene_dict[gname] = cat
        return extraction, gene_dict

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_len = len(content)
    content = preprocess_md(content)
    print(f"  📏 文本预处理: {original_len:,} → {len(content):,} 字符 (节省 {original_len - len(content):,} 字符)")

    # 加载 registry（如果外部没传入）
    if registry is None:
        registry = _load_extraction_registry()

    primary_model = os.getenv("MODEL", "Vendor2/Claude-4.6-opus")

    # 第一次尝试：主 API（classify 和 extract 都用主 API）
    print(f"  🔵 使用主 API ({primary_model}) 提取...")
    extraction, gene_dict, success = _call_extract_api(
        client, primary_model, content, name, registry,
        classify_client=client, classify_model=primary_model,
    )

    # Fallback：整体失败才走 fallback
    if not success and fallback_client:
        print(f"  🔄 主 API 失败，自动切换到 Fallback ({FALLBACK_MODEL})...")
        registry_fallback = _load_extraction_registry()
        extraction, gene_dict, success = _call_extract_api(
            fallback_client, FALLBACK_MODEL, content, name, registry_fallback,
            classify_client=fallback_client, classify_model=FALLBACK_MODEL,
        )

    if not success or extraction is None:
        print(f"  ⚠️  所有 API 均失败: {name}")
        failed_files.append(name)
        os.makedirs(paper_dir, exist_ok=True)
        error_report = {
            "file": name,
            "error": "All APIs failed",
            "timestamp": datetime.now().isoformat(),
        }
        with open(os.path.join(paper_dir, "extraction-error.json"), 'w', encoding='utf-8') as f:
            json.dump(error_report, f, indent=2, ensure_ascii=False)
        return None, None

    # 保存结果
    os.makedirs(paper_dir, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(extraction, f, indent=2, ensure_ascii=False)
    print(f"  ✅ 提取结果已保存: {output_path}")

    if gene_dict:
        gene_dict_path = os.path.join(paper_dir, "gene_dict.json")
        with open(gene_dict_path, 'w', encoding='utf-8') as f:
            json.dump(gene_dict, f, indent=2, ensure_ascii=False)
        print(f"  📋 基因分类字典已保存: {gene_dict_path}")

    return extraction, gene_dict


# ═══════════════════════════════════════════════════════════════════════════════════
#  旧版兼容入口
# ═══════════════════════════════════════════════════════════════════════════════════

def ai_response(path):
    """旧版兼容入口：仅提取，不返回结果。"""
    extract_paper(path)


def resolve_test_files(files):
    """根据 TEST_INDEX 环境变量筛选测试文件。"""
    test_index = os.getenv("TEST_INDEX", "1")
    if test_index.isdigit():
        idx = int(test_index) - 1
        if 0 <= idx < len(files):
            print(f"🧪 测试模式: 仅处理第 {idx + 1} 个文件 → {files[idx]}")
            return [files[idx]]
        else:
            print(f"❌ 编号 {idx + 1} 超出范围 (共 {len(files)} 个文件)")
            return []
    target = test_index if test_index.endswith(".md") else test_index + ".md"
    matched = [f for f in files if f == target]
    if matched:
        print(f"🧪 测试模式: 按文件名匹配 → {matched[0]}")
        return matched
    matched = [f for f in files if test_index in f]
    if matched:
        print(f"🧪 测试模式: 模糊匹配 → {matched[0]}")
        return [matched[0]]
    print(f"❌ 未找到匹配 '{test_index}' 的文件 (共 {len(files)} 个文件)")
    return []


if __name__ == "__main__":
    if not os.path.exists(INPUT_DIR):
        print(f"错误: 输入目录 {INPUT_DIR} 不存在！")
    else:
        files = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith('.md')])
        print(f"找到 {len(files)} 个待处理文件...")

        if os.getenv("TEST_MODE") == "1":
            files = resolve_test_files(files)

        # 加载一次 registry，所有文件共享
        registry = _load_extraction_registry()

        for file in files:
            ai_response(os.path.join(INPUT_DIR, file))

        tracker.print_summary()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tracker.save_report(os.path.join(TOKEN_USAGE_DIR, f"extract-{timestamp}.json"))

        if failed_files:
            print(f"\n{'='*60}")
            print(f"⚠️  以下 {len(failed_files)} 个文件 API 返回空内容，需要重跑:")
            for f in failed_files:
                print(f"     - {f}")
            print(f"   提示: FORCE_RERUN=1 bash scripts/run.sh extract")
            print(f"{'='*60}")
