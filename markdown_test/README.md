# markdown_test

这个文件夹演示如何把 Markdown 转换为 HTML，并自动嵌入到本文档中。

## 文件说明

| 文件 | 作用 |
|------|------|
| `input.md` | 原始 Markdown 输入 |
| `convert.py` | 转换脚本，生成 HTML 并更新本文件 |
| `output.html` | 生成的独立 HTML 页面（浏览器可直接打开） |

## 使用方法

```bash
pip install markdown
python convert.py
```

## 渲染结果（由 convert.py 自动更新）




<!-- RENDER_START -->
```html
<h1>Hello World</h1>
<p>这是一段 <strong>粗体</strong> 和 <em>斜体</em> 文字。</p>
<ul>
<li>列表项 1</li>
<li>列表项 2</li>
</ul>
<h2>代码示例</h2>
<pre><code class="language-python">print(&quot;Hello, Markdown!&quot;)
</code></pre>
```
<!-- RENDER_END -->
