# Next.js + TSX 简化教程

## 核心区别

```
传统 HTML                     →    Next.js TSX
────────────────────────────────────────────────────────
index.html                   →    app/page.tsx
<style>css</style>           →    app/globals.css 或 CSS modules
<script>js</script>          →    组件内的函数和状态
```

## TSX 是什么？

**TSX = TypeScript + XML (HTML-like)**

```tsx
// 这是一个 TSX 组件
export default function Hello() {
  return <h1>你好</h1>  // ← 这部分长得像 HTML，叫 JSX
}
```

## HTML vs TSX 对比

| HTML | TSX | 说明 |
|------|-----|------|
| `<div class="box">` | `<div className="box">` | `class` → `className` |
| `<input type="text">` | `<input type="text" />` | 自闭合标签要加 `/` |
| `<style>.box{...}</style>` | `import './style.css'` | 样式分离 |
| `onclick="func()"` | `onClick={func}` | 事件名用驼峰命名 |

## Next.js 路由规则

```
文件路径                          →  生成的 URL
────────────────────────────────────────────────────────────
src/app/page.tsx                 →  /
src/app/about/page.tsx           →  /about
src/app/papers/[slug]/page.tsx   →  /papers/任意值
src/app/papers/[slug]/page.tsx   →  /papers/test, /papers/abc...
```

## 文件结构

```
tutorial2/
├── package.json          # 项目依赖
├── next.config.js        # Next.js 配置
├── tsconfig.json         # TypeScript 配置
└── src/
    ├── app/
    │   ├── layout.tsx    # 全局布局（所有页面的外层）
    │   ├── page.tsx      # 首页 (/)
    │   └── papers/
    │       └── [slug]/
    │           └── page.tsx  # 论文详情页 (/papers/xxx)
    ├── components/       # 可复用组件
    │   └── PaperCard.tsx
    └── lib/
        └── supabase.ts   # Supabase 客户端
```

## 运行方法

```bash
cd tutorial2
npm install
npm run dev
# 访问 http://localhost:3000
```
