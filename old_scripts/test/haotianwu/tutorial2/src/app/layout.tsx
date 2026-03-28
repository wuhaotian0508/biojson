/**
 * layout.tsx - 全局布局组件
 *
 * 这是 Next.js App Router 的特殊文件
 * 它会包裹所有页面，相当于所有页面的"外框"
 *
 * 重要概念：
 * - 这是一个 React 组件
 * - children 参数代表当前页面的内容
 * - 这里可以放导航栏、页脚等所有页面共用的内容
 */

import type { Metadata } from 'next'
import './globals.css'

// 页面元数据（会变成 HTML 的 <head> 部分）
export const metadata: Metadata = {
  title: '论文标注系统',
  description: '基于 Next.js 和 Supabase 的简化教程',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode  // children 是任意 React 内容
}) {
  return (
    // TSX 中的根元素，lang 属性和 HTML 一样
    <html lang="zh-CN">
      <body>
        {/* 这里是所有页面共用的导航栏 */}
        <header style={{
          background: '#2563eb',
          color: 'white',
          padding: '16px',
          marginBottom: '20px'
        }}>
          <h1 style={{ margin: 0 }}>📄 论文标注系统 (TSX 版)</h1>
        </header>

        {/* children 会被替换成当前页面的内容 */}
        <main style={{ padding: '20px' }}>
          {children}
        </main>

        {/* 共用的页脚 */}
        <footer style={{
          marginTop: '40px',
          padding: '20px',
          textAlign: 'center',
          color: '#666',
          borderTop: '1px solid #eee'
        }}>
          <p>基于 Next.js + Supabase 构建</p>
        </footer>
      </body>
    </html>
  )
}
