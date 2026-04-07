# 如何渲染 Markdown

## Python

### 使用 `markdown` 库

```python
pip install markdown
```

```python
import markdown

md_text = """
# Hello World

这是一段 **粗体** 和 *斜体* 文字。

- 列表项 1
- 列表项 2
"""

html = markdown.markdown(md_text)
print(html)
```

输出：
```html
<h1>Hello World</h1>
<p>这是一段 <strong>粗体</strong> 和 <em>斜体</em> 文字。</p>
<ul>
<li>列表项 1</li>
<li>列表项 2</li>
</ul>
```

将上面的 HTML 嵌入网页展示：

```html
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <title>Markdown 渲染结果</title>
  <style>
    body { font-family: sans-serif; max-width: 600px; margin: 40px auto; }
  </style>
</head>
<body>
  <h1>Hello World</h1>
  <p>这是一段 <strong>粗体</strong> 和 <em>斜体</em> 文字。</p>
  <ul>
    <li>列表项 1</li>
    <li>列表项 2</li>
  </ul>
</body>
</html>
```

或者用 Python 动态生成并写入 HTML 文件：

```python
import markdown

md_text = """
# Hello World

这是一段 **粗体** 和 *斜体* 文字。

- 列表项 1
- 列表项 2
"""

body = markdown.markdown(md_text)

html_page = f"""<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <title>Markdown 渲染结果</title>
  <style>
    body {{ font-family: sans-serif; max-width: 600px; margin: 40px auto; }}
  </style>
</head>
<body>
{body}
</body>
</html>"""

with open("output.html", "w", encoding="utf-8") as f:
    f.write(html_page)

print("已生成 output.html，用浏览器打开即可查看")
```

### 使用 `mistune`（支持更多扩展）

```python
pip install mistune
```

```python
import mistune

md = mistune.create_markdown()
html = md("# Hello, **World**!")
print(html)
```

### 在 Jupyter Notebook 中渲染

```python
from IPython.display import Markdown, display

display(Markdown("# Hello\n\n这是 **Markdown** 内容"))
```

---

## JavaScript / Node.js

### 使用 `marked`

```bash
npm install marked
```

```javascript
import { marked } from 'marked';

const html = marked('# Hello World\n\n这是 **粗体** 文字。');
console.log(html);
```

### 在浏览器中使用 `marked`

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>
<body>
  <div id="output"></div>
  <script>
    const md = `
# Hello World

这是 **粗体** 和 *斜体*。
    `;
    document.getElementById('output').innerHTML = marked.parse(md);
  </script>
</body>
</html>
```

### 使用 `markdown-it`（更安全、可扩展）

```bash
npm install markdown-it
```

```javascript
import MarkdownIt from 'markdown-it';

const md = new MarkdownIt();
const html = md.render('# Hello\n\n这是 **Markdown**。');
console.log(html);
```

---

## React

### 使用 `react-markdown`

```bash
npm install react-markdown
```

```jsx
import ReactMarkdown from 'react-markdown';

function App() {
  const content = `
# 标题

这是 **粗体** 文字。

\`\`\`python
print("Hello, World!")
\`\`\`
  `;

  return <ReactMarkdown>{content}</ReactMarkdown>;
}
```

---

## 命令行工具

### `pandoc`（万能文档转换器）

```bash
# Markdown 转 HTML
pandoc input.md -o output.html

# Markdown 转 PDF
pandoc input.md -o output.pdf

# Markdown 转 Word
pandoc input.md -o output.docx
```

### `glow`（终端中渲染 Markdown）

```bash
# 安装 (macOS)
brew install glow

# 渲染文件
glow README.md

# 渲染标准输入
echo "# Hello **World**" | glow -
```

---

## 在线渲染

| 工具 | 用途 |
|------|------|
| [Typora](https://typora.io) | 桌面端所见即所得编辑器 |
| [VS Code](https://code.visualstudio.com) | `Ctrl+Shift+V` 预览 |
| [StackEdit](https://stackedit.io) | 浏览器在线编辑器 |
| [Dillinger](https://dillinger.io) | 在线实时预览 |

---

## 小结

| 场景 | 推荐工具 |
|------|----------|
| Python 后端 | `markdown` 或 `mistune` |
| Node.js | `marked` 或 `markdown-it` |
| React 前端 | `react-markdown` |
| 文档转换 | `pandoc` |
| 终端查看 | `glow` |
| Jupyter | `IPython.display.Markdown` |
