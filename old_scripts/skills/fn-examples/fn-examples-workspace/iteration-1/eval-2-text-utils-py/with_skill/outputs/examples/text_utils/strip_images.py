"""
strip_images — Remove markdown image tags (both CDN links and local paths).

Source: extractor/text_utils.py:53

Usage:
    python strip_images.py
"""

# --- External Imports ---
import re


# --- Target Function ---

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


# --- Sample Input ---
# A fragment of a MinerU-converted scientific paper containing two common image
# formats: a CDN-hosted image and a local path image, interspersed with real
# text about carotenoid biosynthesis in tomato.

sample_md = """\
# Carotenoid Biosynthesis in Tomato

The pathway from GGPP to lycopene involves four desaturation steps.

![Figure 1: Carotenoid pathway](https://cdn-mineru.openxlab.org.cn/result/abc123/fig1.png)

Overexpression of *CrtI* in tomato fruit increased total carotenoid content by 2.5-fold (Table 1).

![](images/e2f35d9768aa228bf59dd00ff6e7ddcf_table1.png)

The phytoene synthase gene *PSY1* is the rate-limiting enzyme in this pathway.
"""

# --- Run ---
if __name__ == "__main__":
    result = strip_images(sample_md)
    print("=== Original (first 200 chars) ===")
    print(sample_md[:200])
    print()
    print("=== After strip_images ===")
    print(result)
