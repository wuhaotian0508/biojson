# HTML vs TSX 对照表

## 基本语法对比

| HTML | TSX | 说明 |
|------|-----|------|
| `<div class="box">` | `<div className="box">` | `class` 是 JS 关键字 |
| `<label for="id">` | `<label htmlFor="id">` | `for` 是 JS 关键字 |
| `<img src="x.jpg">` | `<img src="x.jpg" />` | 自闭合要加 `/` |
| `<input type="text">` | `<input type="text" />` | 自闭合要加 `/` |
| `<style>.x{color:red}</style>` | `import './style.css'` | 样式分离 |
| `onclick="func()"` | `onClick={func}` | 事件驼峰命名 |
| `onchange="func()"` | `onChange={func}` | 事件驼峰命名 |
| `<div style="color:red">` | `<div style={{color:'red'}}>` | style 是对象 |

## 完整例子对比

### HTML 版本

```html
<!DOCTYPE html>
<html>
<head>
  <title>论文列表</title>
  <style>
    .card { padding: 20px; border: 1px solid #ccc; }
    .title { font-size: 18px; font-weight: bold; }
  </style>
</head>
<body>
  <div id="app">
    <h1>论文列表</h1>
    <div id="papers"></div>
  </div>

  <script>
    fetchPapers().then(papers => {
      const html = papers.map(p => `
        <div class="card">
          <div class="title">${p.title}</div>
          <div>${p.journal}</div>
        </div>
      `).join('')
      document.getElementById('papers').innerHTML = html
    })
  </script>
</body>
</html>
```

### TSX 版本

```tsx
// app/page.tsx
import { supabase } from '@/lib/supabase'

// 数据获取（服务器端）
async function getPapers() {
  const { data } = await supabase.from('papers').select('*')
  return data || []
}

// 页面组件
export default async function HomePage() {
  const papers = await getPapers()

  return (
    <div>
      <h1>论文列表</h1>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {papers.map(paper => (
          <div key={paper.id} style={{ padding: '20px', border: '1px solid #ccc' }}>
            <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
              {paper.title}
            </div>
            <div>{paper.journal}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
```

## TSX 独有的能力

### 1. 条件渲染

```tsx
// HTML 需要用 JavaScript 拼接字符串
<div id="result"></div>
<script>
  document.getElementById('result').innerHTML =
    papers.length === 0 ? '<p>没有数据</p>' : renderList(papers)
</script>

// TSX 可以直接在 JSX 中写逻辑
{papers.length === 0 ? (
  <p>没有数据</p>
) : (
  papers.map(p => <PaperCard key={p.id} paper={p} />)
)}
```

### 2. 组件复用

```tsx
// 定义一个可复用的组件
function PaperCard({ paper }: { paper: Paper }) {
  return (
    <div style={{ padding: '20px', border: '1px solid #ccc' }}>
      <h3>{paper.title}</h3>
    </div>
  )
}

// 在多处使用
{papers.map(paper => (
  <PaperCard key={paper.id} paper={paper} />
))}
```

### 3. 样式对象

```tsx
// HTML
<div style="color: red; font-size: 14px; padding: 10px;">

// TSX (用对象，属性名用驼峰)
<div style={{
  color: 'red',
  fontSize: '14px',      // font-size → fontSize
  paddingTop: '10px'     // padding-top → paddingTop
}}>
```

### 4. 表达式插值

```tsx
// HTML
<p>共 <span id="count"></span> 篇论文</p>
<script>document.getElementById('count').textContent = papers.length</script>

// TSX (用花括号)
<p>共 {papers.length} 篇论文</p>
```

## 常见错误

| ❌ 错误 | ✅ 正确 | 原因 |
|--------|--------|------|
| `<div class="x">` | `<div className="x">` | class 是关键字 |
| `<label for="x">` | `<label htmlFor="x">` | for 是关键字 |
| `style="color:red"` | `style={{color:'red'}}` | style 是对象 |
| `<img src="x.jpg">` | `<img src="x.jpg" />` | 需要 `/` |
| `return <div>A</div><div>B</div>` | `return <><div>A</div><div>B</div></>` | 需要根元素 |

## 快速记忆口诀

```
class 要写 className
for 要写 htmlFor
标签自闭合加 /
style 是对象不是串
属性名统统驼峰命
表达式花括号包裹
组件名大写开头
```
