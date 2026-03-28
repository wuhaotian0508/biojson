"""
strip_acknowledgments — Remove the Acknowledgments/Acknowledgements section from
markdown, preserving any sections that follow it.

Source: extractor/text_utils.py:122

Usage:
    python strip_acknowledgments.py
"""

# --- External Imports ---
import re


# --- Target Function ---

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


# --- Sample Input ---
# A paper fragment that includes an Acknowledgments section (American spelling)
# followed by a Supplementary Materials section that should be preserved.

sample_md = """\
# Discussion

The SlMYB12 transcription factor activates flavonol biosynthesis genes in tomato.

# Acknowledgments

We thank Dr. J. Giovannoni for providing tomato seeds and Dr. Y. Liu for
helpful discussions. This work was supported by the National Natural Science
Foundation of China (Grant No. 31872120).

# Supplementary Materials

Table S1. List of all primers used for qRT-PCR experiments.
Figure S1. Phylogenetic tree of MYB transcription factors in Solanaceae.
"""

# --- Run ---
if __name__ == "__main__":
    result = strip_acknowledgments(sample_md)
    print("=== Original ===")
    print(sample_md)
    print()
    print("=== After strip_acknowledgments ===")
    print(result)
    print()

    # Also test British spelling variant (Acknowledgements) and ## heading
    sample_british = """\
# Methods

Total RNA was extracted using TRIzol reagent.

## Acknowledgements

The authors acknowledge funding from the Biotechnology and Biological Sciences
Research Council (BBSRC, UK).
"""
    result2 = strip_acknowledgments(sample_british)
    print("=== British spelling '## Acknowledgements' (no trailing section) ===")
    print(result2)
