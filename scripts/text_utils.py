"""
text_utils.py
文本预处理工具：去除论文 Markdown 中的无用内容，减少 token 消耗。

对外只暴露一个入口函数 preprocess_md()，内部调用各子函数。
以后新增预处理规则只需改这一个文件。

当前预处理步骤：
    1. strip_images        — 去除图片标签（两种格式）
    2. strip_urls          — 去除括号内的 URL（http/https 链接）
    3. strip_references    — 去除 References / Literature Cited 引用列表
    4. strip_acknowledgments — 去除 Acknowledgments 段落
    5. strip_extra_blanks  — 合并多余空行
"""

import re


# ═══════════════════════════════════════════════════════════════════════════════
#  对外入口
# ═══════════════════════════════════════════════════════════════════════════════

def preprocess_md(md_content):
    """
    一站式 Markdown 预处理：去除 MinerU 转换产生的所有无用内容。

    调用方只需：
        from text_utils import preprocess_md
        content = preprocess_md(raw_md)

    Args:
        md_content: MinerU 转换后的 Markdown 全文

    Returns:
        清理后的文本（图片、引用列表、致谢 已去除，多余空行已合并）
    """
    content = strip_images(md_content)
    content = strip_urls(content)
    content = strip_references(content)
    content = strip_acknowledgments(content)
    content = strip_extra_blanks(content)
    return content


# ═══════════════════════════════════════════════════════════════════════════════
#  子函数
# ═══════════════════════════════════════════════════════════════════════════════

def strip_images(md_content):
    """
    去除 Markdown 图片标签。

    MinerU 有两种图片格式：
        1. ![image](https://cdn-mineru.openxlab.org.cn/result/...)   — CDN 链接
        2. ![](images/e2f35d9768aa228bf59dd00ff6e7ddcf...)           — 本地路径

    统一用一条正则匹配：![ 任意alt ]( 任意路径 )
    """
    result = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', md_content)
    return result


def strip_urls(md_content):
    """
    去除括号内的 URL 链接。

    MinerU 转换的论文中常包含大量括号内 URL，如：
        (https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE147589)
        (https://doi.org/10.5281/zenodo.5237316)
        (http://www.plantcell.org)

    这些对基因信息提取无用，且浪费 token。
    匹配 (http://...) 或 (https://...) 整体替换为空。
    """
    return re.sub(r'\(https?://[^)]*\)', '', md_content)


def strip_references(md_content):
    """
    去除 References / Literature Cited 引用列表，保留后面有用的 section。

    匹配的标题变体：
        # References / # REFERENCES / # References and Notes
        # LITERATURE CITED / # Literature Cited

    规则：
        - 从匹配的标题开始删除
        - 遇到下一个 `# ` + 大写字母开头的标题则停止删除，保留该标题及之后内容
        - 如果后面没有其他标题，直接截断
    """
    ref_pattern = re.compile(
        r'^#{1,2}\s+'
        r'(?:'
        r'References?\s*(?:and\s*notes)?'
        r'|'
        r'Literature\s+Cited'
        r')\s*$',
        re.MULTILINE | re.IGNORECASE
    )
    ref_match = ref_pattern.search(md_content)

    if not ref_match:
        return md_content

    ref_start = ref_match.start()
    after_ref = md_content[ref_match.end():]

    # 找下一个 `# ` + 大写字母开头的标题
    next_heading = re.search(r'^#\s+[A-Z]', after_ref, re.MULTILINE)

    if next_heading:
        kept_after = after_ref[next_heading.start():]
        return md_content[:ref_start].rstrip() + "\n\n" + kept_after
    else:
        return md_content[:ref_start].rstrip()


def strip_acknowledgments(md_content):
    """
    去除 Acknowledgments 段落。

    匹配的标题变体：
        # ACKNOWLEDGMENTS / # Acknowledgments / # Acknowledgements（英式拼写）
        ## ACKNOWLEDGMENTS（二级标题也匹配）

    规则同 strip_references：删到下一个 # 大写标题为止。
    """
    ack_pattern = re.compile(
        r'^#{1,2}\s+Acknowledg[e]?ments?\s*$',
        re.MULTILINE | re.IGNORECASE
    )
    ack_match = ack_pattern.search(md_content)

    if not ack_match:
        return md_content

    ack_start = ack_match.start()
    after_ack = md_content[ack_match.end():]

    next_heading = re.search(r'^#\s+[A-Z]', after_ack, re.MULTILINE)

    if next_heading:
        kept_after = after_ack[next_heading.start():]
        return md_content[:ack_start].rstrip() + "\n\n" + kept_after
    else:
        return md_content[:ack_start].rstrip()


def strip_extra_blanks(md_content):
    """合并 3 个以上连续空行为 2 个空行。"""
    return re.sub(r'\n{3,}', '\n\n', md_content)
