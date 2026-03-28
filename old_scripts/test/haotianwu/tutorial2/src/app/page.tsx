/**
 * page.tsx - 首页组件
 *
 * 这是访问 "/" 路径时显示的页面
 *
 * TSX 语法要点：
 * 1. 文件名是 .tsx (TypeScript + XML)
 * 2. export default 导出一个函数组件
 * 3. 函数返回的 JSX 会被渲染成 HTML
 * 4. 可以用 async 函数，Next.js 会处理数据获取
 */

import { supabase, type Paper } from '@/lib/supabase'
import Link from 'next/link'  // Next.js 的链接组件（比 <a> 标签更快）

// ===== 数据获取函数（在服务器端运行）=====
// 这是一个 async 函数，Next.js 会在渲染页面前调用它
async function getPapers(): Promise<Paper[]> {
  const { data, error } = await supabase
    .from('papers')
    .select('*')
  // .order('created_at', { ascending: false })  // 按时间倒序

  if (error) {
    console.error('获取数据失败:', error)
    return []
  }

  return (data || []) as Paper[]
}

// ===== 页面组件 =====
// 这是 async 函数组件，Next.js 15+ 支持
export default async function HomePage() {
  // 等待数据获取完成
  const papers = await getPapers()

  // 组件返回的 JSX 会被渲染成 HTML
  return (
    <div>
      {/* JSX 中的注释用 {/* ... *} */}
      {/* style 属性要用对象，不是字符串！ */}
      <div style={{ marginBottom: '24px' }}>
        <h2>论文列表</h2>
        <p style={{ color: '#666' }}>
          共 {papers.length} 篇论文
        </p>
      </div>

      {/* 条件渲染：用三元运算符 */}
      {papers.length === 0 ? (
        // 如果没有数据，显示这个
        <div style={{
          padding: '60px',
          textAlign: 'center',
          color: '#999'
        }}>
          <p style={{ fontSize: '48px' }}>📭</p>
          <p>暂无论文数据</p>
        </div>
      ) : (
        // 如果有数据，显示列表
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* map 循环渲染列表 */}
          {papers.map((paper) => (
            // 必须有 key 属性！
            <Link
              key={paper.id}
              href={`/papers/${paper.slug}`}
              // style 接受对象，className 接受字符串
              style={{
                display: 'block',
                textDecoration: 'none',  // 去掉下划线
                color: 'inherit'
              }}
            >
              {/* PaperCard 组件 */}
              <div style={{
                background: 'white',
                padding: '20px',
                borderRadius: '8px',
                border: '2px solid transparent',
                cursor: 'pointer',
                // :hover 效果在 style 中比较麻烦，这里简化
              }}>
                {/* 论文标题 */}
                <h3 style={{ margin: '0 0 8px 0', color: '#1a1a1a' }}>
                  {paper.title || paper.slug}
                  {/* TSX 中用 || 处理空值，而不是 ?? */}
                </h3>

                {/* 论文元信息 */}
                <div style={{ fontSize: '14px', color: '#666', marginBottom: '12px' }}>
                  {paper.journal || '未知期刊'}
                  {paper.doi && ` · DOI: ${paper.doi}`}
                </div>

                {/* 统计信息 */}
                <div style={{ display: 'flex', gap: '16px' }}>
                  <span style={{
                    background: '#f0f0f0',
                    padding: '4px 12px',
                    borderRadius: '12px',
                    fontSize: '13px'
                  }}>
                    🧬 {paper.gene_count || 0} 个基因
                  </span>
                  <span style={{
                    background: '#f0f0f0',
                    padding: '4px 12px',
                    borderRadius: '12px',
                    fontSize: '13px'
                  }}>
                    📋 {paper.status || 'pending'}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

/*
 * ========== HTML vs TSX 对比 ==========
 *
 * HTML:
 *   <div class="box" onclick="func()">内容</div>
 *   <img src="pic.jpg">
 *
 * TSX:
 *   <div className="box" onClick={func}>内容</div>
 *   <img src="pic.jpg" />
 *
 * 关键区别：
 *   1. class → className (class 是 JS 关键字)
 *   2. onclick → onClick (驼峰命名)
 *   3. 自闭合标签必须加 />
 *   4. style 是对象，不是字符串
 *   5. 可以用 { } 包裹 JS 表达式
 */
