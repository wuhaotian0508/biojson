/**
 * papers/[slug]/page.tsx - 动态路由页面
 *
 * 文件夹名 [slug] 表示动态参数！
 * 访问 /papers/test 时，slug = "test"
 * 访问 /papers/abc 时，slug = "abc"
 *
 * Next.js 会把 URL 中的参数作为 props 传给组件
 */

import { supabase, type Paper, type Gene } from '@/lib/supabase'
import Link from 'next/link'

// 组件的 props 类型定义
interface PageProps {
  params: {
    slug: string  // 这就是 [slug] 对应的值
  }
}

// 获取论文数据
async function getPaper(slug: string): Promise<{ paper: Paper | null, genes: Gene[] }> {
  // 同时获取论文和基因数据（并行请求）
  const [paperResult, genesResult] = await Promise.all([
    supabase.from('papers').select('*').eq('slug', slug).single(),
    supabase.from('genes').select('*').eq('paper_id', slug)  // 假设 paper_id 就是 slug
  ])

  return {
    paper: paperResult.data,
    genes: genesResult.data || []
  }
}

// 页面组件
export default async function PaperDetailPage({ params }: PageProps) {
  const { slug } = params  // 从 URL 获取动态参数
  const { paper, genes } = await getPaper(slug)

  // 如果论文不存在
  if (!paper) {
    return (
      <div style={{ textAlign: 'center', padding: '60px' }}>
        <p style={{ fontSize: '48px' }}>😕</p>
        <h2>论文不存在</h2>
        <p>找不到 slug 为 "{slug}" 的论文</p>
        <Link href="/" style={{ color: '#2563eb' }}>返回首页</Link>
      </div>
    )
  }

  return (
    <div>
      {/* 返回链接 */}
      <Link
        href="/"
        style={{
          display: 'inline-block',
          marginBottom: '20px',
          color: '#2563eb',
          textDecoration: 'none'
        }}
      >
        ← 返回列表
      </Link>

      {/* 论文标题和元信息 */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '28px', marginBottom: '16px' }}>
          {paper.title || paper.slug}
        </h1>
        <div style={{ color: '#666', lineHeight: '1.6' }}>
          <p>{paper.journal || '未知期刊'}</p>
          {paper.doi && <p>DOI: {paper.doi}</p>}
        </div>
      </div>

      {/* 基因列表 */}
      <div>
        <h2 style={{ marginBottom: '16px' }}>
          基因数据 ({genes.length} 个)
        </h2>

        {genes.length === 0 ? (
          <p style={{ color: '#999' }}>暂无基因数据</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {genes.map((gene) => (
              <GeneCard key={gene.id} gene={gene} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ===== 子组件：基因卡片 =====
// 注意：组件名必须大写开头！
function GeneCard({ gene }: { gene: Gene }) {
  // gene_data 是一个 JSON 对象，包含各种字段
  const geneData = gene.gene_data || {}
  const geneName = geneData.Gene_Name || geneData.gene_name || `Gene ${gene.gene_index}`

  return (
    <div style={{
      background: 'white',
      border: '1px solid #eee',
      borderRadius: '8px',
      padding: '16px'
    }}>
      {/* 基因名称 */}
      <h3 style={{ margin: '0 0 12px 0', fontSize: '18px' }}>
        🧬 {geneName}
      </h3>

      {/* 基因字段列表 */}
      {Object.entries(geneData).map(([key, value]) => {
        // 跳过已经显示为标题的 Gene_Name
        if (key === 'Gene_Name' || key === 'gene_name') return null

        // 处理数组类型的值
        const displayValue = Array.isArray(value) ? value.join(', ') : (value ?? 'NA')

        return (
          <div key={key} style={{ marginBottom: '8px' }}>
            <div style={{ fontWeight: 600, fontSize: '14px', color: '#444' }}>
              {key}
            </div>
            <div style={{
              padding: '8px 12px',
              background: '#f9f9f9',
              borderRadius: '4px',
              fontFamily: 'monospace',
              fontSize: '14px'
            }}>
              {displayValue}
            </div>
          </div>
        )
      })}
    </div>
  )
}

/*
 * ========== 动态路由说明 ==========
 *
 * 文件结构：
 *   app/
 *     papers/
 *       [slug]/
 *         page.tsx
 *
 * URL 映射：
 *   /papers/test     → params.slug = "test"
 *   /papers/abc123   → params.slug = "abc123"
 *   /papers/任意值   → params.slug = "任意值"
 *
 * 多个动态参数：
 *   app/users/[id]/posts/[postId]/page.tsx
 *   → /users/123/posts/456
 *   → params.id = "123", params.postId = "456"
 */
