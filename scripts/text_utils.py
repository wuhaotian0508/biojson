"""
text_utils.py
文本预处理工具：去除 References 引用列表，保留后面有用的 section。

规则：
    - References 开始标志：`# REFERENCES` (或变体如 # References, # REFERENCES AND NOTES)
    - References 结束标志：下一个 `# ` + 大写字母开头的标题
    - 删除 References 标题到结束标志之间的内容（引用列表）
    - 保留结束标志及之后的所有内容（如 STAR Methods 等）
"""

import re


def strip_references(md_content):
    """
    去除 References 引用列表，保留后面有用的 section。
    
    Args:
        md_content: Markdown 格式的论文全文
    
    Returns:
        去除引用列表后的文本
    """
    # 1. 找到 References 标题（# References / # REFERENCES / # REFERENCES AND NOTES 等）
    ref_pattern = re.compile(
        r'^(#{1,2}\s+References?\s*(and\s*notes)?\s*)$',
        re.MULTILINE | re.IGNORECASE
    )
    ref_match = ref_pattern.search(md_content)
    
    if not ref_match:
        # 没有 References section，原样返回
        return md_content
    
    ref_start = ref_match.start()
    after_ref = md_content[ref_match.end():]
    
    # 2. 在 References 之后，找下一个 `# ` + 大写字母开头的标题
    next_heading = re.search(r'^#\s+[A-Z]', after_ref, re.MULTILINE)
    
    if next_heading:
        # 保留 References 之前的内容 + References 之后下一个有用标题开始的内容
        kept_after = after_ref[next_heading.start():]
        result = md_content[:ref_start].rstrip() + "\n\n" + kept_after
    else:
        # References 之后没有其他一级大写标题，直接截断到 References 之前
        result = md_content[:ref_start].rstrip()
    
    return result
