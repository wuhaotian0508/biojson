#!/usr/bin/env python3
"""测试参考文献匹配修复"""

import re

# 直接复制 Agent 的静态方法进行测试
def _extract_sources_from_tool_results(tool_results: list[dict]) -> list[dict]:
    """从工具调用结果中提取参考文献来源（PubMed、gene_db 等）。"""
    sources = []

    for tr in tool_results:
        tool_name = tr.get("tool", "")
        content = tr.get("content", "")

        if tool_name == "pubmed_search":
            blocks = re.split(r'\n\[(\d+)\]\s+', content)
            for i in range(1, len(blocks), 2):
                tool_index = blocks[i]
                block = blocks[i + 1] if i + 1 < len(blocks) else ""
                title_line = block.split('\n')[0].strip()
                pmid_match = re.search(r'PMID:\s*(\d+)', block)
                url_match = re.search(r'链接:\s*(https?://\S+)', block)
                journal_match = re.search(r'期刊:\s*(.+)', block)
                sources.append({
                    "source_type": "pubmed",
                    "title": title_line,
                    "paper_title": title_line,
                    "pmid": pmid_match.group(1) if pmid_match else "",
                    "url": url_match.group(1) if url_match else "",
                    "journal": journal_match.group(1).strip() if journal_match else "",
                    "doi": "",
                    "tool_index": int(tool_index),
                })

    return sources

def _filter_cited_sources(answer_text: str, all_sources: list[dict]) -> list[dict]:
    """从回答文本中提取实际引用的编号，过滤并重排 sources 列表。"""
    cited_numbers = set()
    for match in re.finditer(r'\[(\d+)\]', answer_text):
        cited_numbers.add(int(match.group(1)))

    if not cited_numbers:
        return []

    cited_sources = []
    for num in sorted(cited_numbers):
        for source in all_sources:
            if source.get("tool_index") == num:
                cited_sources.append(source)
                break

    return cited_sources

# 模拟工具输出（包含19篇文献）
mock_tool_results = [
    {
        "tool": "pubmed_search",
        "content": """PubMed 搜索结果（共 19 篇）：

[1] First Paper Title
    期刊: Nature
    PMID: 11111111
    链接: https://pubmed.ncbi.nlm.nih.gov/11111111/

[2] Second Paper Title
    期刊: Science
    PMID: 22222222
    链接: https://pubmed.ncbi.nlm.nih.gov/22222222/

[3] Third Paper Title
    期刊: Cell
    PMID: 33333333
    链接: https://pubmed.ncbi.nlm.nih.gov/33333333/

[17] Seventeenth Paper Title
    期刊: PNAS
    PMID: 17171717
    链接: https://pubmed.ncbi.nlm.nih.gov/17171717/

[19] Nineteenth Paper Title
    期刊: Plant Cell
    PMID: 19191919
    链接: https://pubmed.ncbi.nlm.nih.gov/19191919/
"""
    }
]

# 模拟 LLM 回答（只引用了 [1], [3], [17]）
mock_answer = """
根据研究 [1]，该基因在植物中起关键作用。
进一步的实验 [3] 证实了这一点。
最新的综述 [17] 总结了相关进展。
"""

print("=" * 60)
print("测试：参考文献匹配修复")
print("=" * 60)

# 1. 提取所有来源
all_sources = Agent._extract_sources_from_tool_results(mock_tool_results)
print(f"\n1. 从工具输出提取的所有来源数量: {len(all_sources)}")
for s in all_sources:
    print(f"   [{s['tool_index']}] {s['title']}")

# 2. 过滤实际引用的来源
cited_sources = Agent._filter_cited_sources(mock_answer, all_sources)
print(f"\n2. 回答中实际引用的来源数量: {len(cited_sources)}")
for s in cited_sources:
    print(f"   [{s['tool_index']}] {s['title']}")

# 3. 验证结果
print("\n3. 验证结果:")
expected_indices = [1, 3, 17]
actual_indices = [s['tool_index'] for s in cited_sources]

if actual_indices == expected_indices:
    print("   ✅ 通过！引用编号匹配正确")
    print(f"   期望: {expected_indices}")
    print(f"   实际: {actual_indices}")
else:
    print("   ❌ 失败！引用编号不匹配")
    print(f"   期望: {expected_indices}")
    print(f"   实际: {actual_indices}")
    sys.exit(1)

print("\n" + "=" * 60)
print("测试通过！")
print("=" * 60)
