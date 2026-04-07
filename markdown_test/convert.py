"""
convert.py
----------
将 input.md 转换为 HTML，生成 output.html，
并同时更新 README.md，把渲染结果嵌入文档中。

用法：
    python convert.py
"""

import markdown
import re
from pathlib import Path

HERE = Path(__file__).parent
INPUT_MD   = HERE / "input.md"
OUTPUT_HTML = HERE / "output.html"
README_MD  = HERE / "README.md"

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <title>Markdown 渲染结果</title>
  <style>
    body {{ font-family: sans-serif; max-width: 660px; margin: 40px auto; line-height: 1.7; }}
    code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
    pre  {{ background: #f4f4f4; padding: 12px; border-radius: 6px; overflow-x: auto; }}
  </style>
</head>
<body>
{body}
</body>
</html>"""

# ── 1. 读取 Markdown ──────────────────────────────────────────────
md_text = INPUT_MD.read_text(encoding="utf-8")

# ── 2. 转换为 HTML 片段 ───────────────────────────────────────────
body = markdown.markdown(md_text, extensions=["fenced_code"])

# ── 3. 写入独立 HTML 文件 ─────────────────────────────────────────
OUTPUT_HTML.write_text(HTML_TEMPLATE.format(body=body), encoding="utf-8")
print(f"✓ 生成 {OUTPUT_HTML.name}")

# ── 4. 把 HTML 片段嵌入 README.md 的占位符之间 ────────────────────
#
#  README.md 中需要有这两行标记：
#    <!-- RENDER_START -->
#    <!-- RENDER_END -->
#  脚本会把它们之间的内容替换为最新的 HTML 片段。
#
readme = README_MD.read_text(encoding="utf-8")

block = f"\n<!-- RENDER_START -->\n```html\n{body}\n```\n<!-- RENDER_END -->"

# 如果标记已存在就替换，否则追加到末尾
if "<!-- RENDER_START -->" in readme:
    readme = re.sub(
        r"<!-- RENDER_START -->.*?<!-- RENDER_END -->",
        block,
        readme,
        flags=re.DOTALL,
    )
else:
    readme += "\n" + block + "\n"

README_MD.write_text(readme, encoding="utf-8")
print(f"✓ 更新 {README_MD.name}")
print("完成！用浏览器打开 output.html 可直接查看渲染效果。")
