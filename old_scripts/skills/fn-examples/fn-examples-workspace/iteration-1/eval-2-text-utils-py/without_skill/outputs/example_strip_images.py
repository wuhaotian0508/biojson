#!/usr/bin/env python3
"""
Example: strip_images()

Removes Markdown image tags from text.
Handles both CDN URL images and local path images produced by MinerU.

Signature:
    strip_images(md_content: str) -> str
"""
import sys, os
sys.path.insert(0, '/data/haotianwu/biojson')

from extractor.text_utils import strip_images

# ── Example 1: CDN image link (typical MinerU output) ─────────────────────────
text_cdn = """\
Some important gene findings here.

![image](https://cdn-mineru.openxlab.org.cn/result/abc123/figure1.png)

The OsCHI gene was overexpressed in tomato fruit.
"""

result1 = strip_images(text_cdn)
print("=== Example 1: CDN image link ===")
print(repr(result1))
print()

# ── Example 2: Local path image ──────────────────────────────────────────────
text_local = """\
Results showed that ![](images/e2f35d9768aa228bf59dd00ff6e7ddcf.png) the concentration increased.
"""

result2 = strip_images(text_local)
print("=== Example 2: Local path image ===")
print(repr(result2))
print()

# ── Example 3: Multiple images with alt text ─────────────────────────────────
text_multi = """\
# Figure Legends

![Figure 1: Pathway overview](figures/fig1.png)

Some text between figures.

![Figure 2: Expression levels](https://example.com/fig2.jpg)

More text after.
"""

result3 = strip_images(text_multi)
print("=== Example 3: Multiple images with alt text ===")
print(result3)

# ── Example 4: Text with no images (no-op) ──────────────────────────────────
text_no_images = "This text has no images at all."
result4 = strip_images(text_no_images)
print("=== Example 4: No images (unchanged) ===")
print(repr(result4))
assert result4 == text_no_images, "Text without images should be unchanged"
print("PASS: text unchanged when no images present")
