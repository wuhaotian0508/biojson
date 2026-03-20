#!/usr/bin/env python3

'''
1. 技能本质上是什么？
一个技能就是一个构造指令包，通常包含：
my-skill/
├── SKILL.md          # 核心：触发条件 + 执行指令
├── scripts/          # 可选：可执行的脚本
├── references/       # 可选：补充文档
└── assets/           # 可选：模板、字体等资源
其中SKILL.md有关键部分：YAML前置两个元数据（名称+描述）和Markdown正文（具体指令）。
2.让Agent支持技能的核心架构
你需要实现三个模块：
①技能注册与发现——扫描技能目录，提取每个技能的name和description，形成一个简单的技能列表注入到Agent的系统提示中。这部分要保留产品，大约每个技能只放100词左右的描述。
②技能路由（触发判断） ——当用户发出来请求时，Agent根据技能列表中的描述判断是否需要调用某个技能。判断逻辑可以是LLM自身推理（像Claude这样直接在提示里列出available_skills让模型自己选），也可以用嵌入相似度匹配做预筛选。
③ 渐进式加载（Progressive Disclosure） — 关键设计。分三层加载：
• 第一层：始终位于上下文中的元数据（名称+描述），用于触发判断
• 第二层：触发后才读取的SKILL.md正文，包含详细指令
• 第三层：继续读取参考文档、脚本等资源
这样做的好处是不会让大量技能内容撑爆上下文窗口。
'''


"""检查所有 extraction.json 的质量，检测字符串数组等常见问题。"""

import json
import os
import sys

REPORTS_DIR = os.getenv("REPORTS_DIR", "/data/haotianwu/biojson/reports")
GENE_KEYS = ("Common_Genes", "Pathway_Genes", "Regulation_Genes", "Genes")

def check_file(path):
    """检查单个 extraction.json，返回问题列表。"""
    issues = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"JSON 解析失败: {e}"]

    if not isinstance(data, dict):
        return [f"顶层不是 dict，而是 {type(data).__name__}"]

    total_genes = 0
    for key in GENE_KEYS:
        arr = data.get(key)
        if arr is None:
            continue

        # 检测：整个数组是字符串而非列表
        if isinstance(arr, str):
            issues.append(f"⚠️  {key} 是字符串而非列表 (长度 {len(arr)})")
            continue

        if not isinstance(arr, list):
            issues.append(f"⚠️  {key} 类型异常: {type(arr).__name__}")
            continue

        total_genes += len(arr)

        # 检测：数组中的元素是字符串而非对象
        str_count = sum(1 for g in arr if isinstance(g, str))
        if str_count > 0:
            issues.append(
                f"❌ {key}: {str_count}/{len(arr)} 个基因是字符串而非对象"
            )

        # 检测：对象中缺少关键字段
        for i, gene in enumerate(arr):
            if isinstance(gene, dict) and "Gene_Name" not in gene:
                issues.append(f"⚠️  {key}[{i}] 缺少 Gene_Name 字段")

    if total_genes == 0:
        issues.append("⚠️  所有基因数组均为空")

    return issues


def main():
    if not os.path.exists(REPORTS_DIR):
        print(f"❌ 报告目录不存在: {REPORTS_DIR}")
        sys.exit(1)

    all_ok = True
    checked = 0

    for dirname in sorted(os.listdir(REPORTS_DIR)):
        extraction_path = os.path.join(REPORTS_DIR, dirname, "extraction.json")
        if not os.path.isfile(extraction_path):
            continue

        checked += 1
        issues = check_file(extraction_path)

        if issues:
            all_ok = False
            print(f"\n📄 {dirname}/extraction.json")
            for issue in issues:
                print(f"   {issue}")
        else:
            print(f"  ✅ {dirname}")

    print(f"\n{'='*50}")
    print(f"检查完毕: {checked} 个文件")
    if all_ok:
        print("🎉 所有文件均无问题！")
    else:
        print("⚠️  存在问题文件，请查看上方详情。")


if __name__ == "__main__":
    main()
