"""
strip_urls — Remove parenthesized HTTP/HTTPS URLs from markdown text.

Source: extractor/text_utils.py:67

Usage:
    python strip_urls.py
"""

# --- External Imports ---
import re


# --- Target Function ---

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


# --- Sample Input ---
# A paragraph from a plant biology paper that contains inline URLs in
# parentheses — common in MinerU-converted papers. These URLs link to
# GEO datasets, DOIs, and journal sites but carry no gene-extraction value.

sample_md = """\
RNA-seq data have been deposited in the GEO database (https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE147589). \
The custom scripts used in this study are available at Zenodo (https://doi.org/10.5281/zenodo.5237316).

For details on flavonoid analysis, see the Plant Cell website (http://www.plantcell.org) and the \
supplementary dataset (https://data.mendeley.com/datasets/xyz789/1).

The gene *SlMYB12* was cloned from cultivar M82 (GenBank accession NM_001247741).
"""

# --- Run ---
if __name__ == "__main__":
    result = strip_urls(sample_md)
    print("=== Original ===")
    print(sample_md)
    print()
    print("=== After strip_urls ===")
    print(result)
