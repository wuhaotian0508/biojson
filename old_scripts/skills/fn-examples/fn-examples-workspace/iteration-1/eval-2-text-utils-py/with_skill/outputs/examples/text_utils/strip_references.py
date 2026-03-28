"""
strip_references — Remove the References / Literature Cited section from markdown,
preserving any sections that follow it.

Source: extractor/text_utils.py:82

Usage:
    python strip_references.py
"""

# --- External Imports ---
import re


# --- Target Function ---

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


# --- Sample Input ---
# A simplified scientific paper in markdown. The References section contains
# typical citation entries. After References there is a Supplementary Materials
# section that should be preserved.

sample_md = """\
# Results

Overexpression of *OsNAS2* increased iron content in polished rice by 3.4-fold.

The transgenic lines also showed elevated zinc levels in both brown and polished rice.

# Discussion

These findings demonstrate that nicotianamine synthase genes can be used to
biofortify rice with both iron and zinc simultaneously.

# References

1. Johnson AAT et al. (2011) Constitutive overexpression of OsNAS gene family.
   Plant Physiol 155: 1839-1847.
2. Lee S et al. (2009) Iron fortification of rice seeds through activation of
   nicotianamine synthase. PNAS 106: 22014-22019.
3. Masuda H et al. (2013) Iron-biofortification in rice by the introduction
   of three barley genes. Plant Sci 132: 141-149.

# Supplementary Materials

Table S1. Primer sequences used for qRT-PCR analysis of iron homeostasis genes.
"""

# --- Run ---
if __name__ == "__main__":
    result = strip_references(sample_md)
    print("=== Original ===")
    print(sample_md)
    print()
    print("=== After strip_references ===")
    print(result)
    print()

    # Also test with "Literature Cited" variant and no following section
    sample_no_trailing = """\
# Methods

Seeds were grown in hydroponic culture for 30 days.

## Literature Cited

- Goto F et al. (1999) Iron accumulation in tobacco. Nat Biotechnol 17: 282-286.
- Drakakaki G et al. (2005) Endosperm phytase. Plant Mol Biol 59: 869-880.
"""
    result2 = strip_references(sample_no_trailing)
    print("=== 'Literature Cited' variant (no trailing section) ===")
    print(result2)
