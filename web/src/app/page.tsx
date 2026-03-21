import { supabase } from '@/lib/supabase'
import Link from 'next/link'

// 论文列表页面 - 首页
export const revalidate = 60 // ISR: 每 60 秒重新验证

interface PaperSummary {
  id: string
  slug: string
  title: string | null
  journal: string | null
  doi: string | null
  gene_count: number
  status: string
  verification_report: {
    summary?: {
      total_fields: number
      supported: number
      unsupported: number
      uncertain: number
      total_corrections: number
    }
  } | null
}

async function getPapers(): Promise<PaperSummary[]> {
  const { data, error } = await supabase
    .from('papers')
    .select('id, slug, title, journal, doi, gene_count, status, verification_report')
    .order('created_at', { ascending: false })

  if (error) {
    console.error('Failed to fetch papers:', error)
    return []
  }
  return (data || []) as PaperSummary[]
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; color: string }> = {
    pending: { label: '待审核', color: 'bg-yellow-100 text-yellow-800' },
    in_review: { label: '审核中', color: 'bg-blue-100 text-blue-800' },
    completed: { label: '已完成', color: 'bg-green-100 text-green-800' },
  }
  const { label, color } = config[status] || config.pending
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${color}`}>
      {label}
    </span>
  )
}

function VerificationBar({ summary }: { summary: PaperSummary['verification_report'] }) {
  if (!summary?.summary) return null
  const { supported, unsupported, uncertain, total_fields } = summary.summary
  if (total_fields === 0) return null

  const pctS = (supported / total_fields) * 100
  const pctU = (uncertain / total_fields) * 100
  const pctN = (unsupported / total_fields) * 100

  return (
    <div className="mt-2">
      <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)] mb-1">
        <span>✅ {supported}</span>
        <span>❓ {uncertain}</span>
        <span>❌ {unsupported}</span>
        <span className="ml-auto">{total_fields} 字段</span>
      </div>
      <div className="w-full h-2 rounded-full bg-[var(--muted)] overflow-hidden flex">
        <div className="bg-green-500 h-full" style={{ width: `${pctS}%` }} />
        <div className="bg-yellow-400 h-full" style={{ width: `${pctU}%` }} />
        <div className="bg-red-400 h-full" style={{ width: `${pctN}%` }} />
      </div>
    </div>
  )
}

export default async function HomePage() {
  const papers = await getPapers()

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold mb-2">📄 论文列表</h1>
        <p className="text-[var(--muted-foreground)]">
          共 {papers.length} 篇论文 · 点击查看详情和标注
        </p>
        <p className="text-sm text-[var(--muted-foreground)] mt-2">
          当前列表按导入时间倒序排列；已额外显示 slug，方便区分新旧数据。
        </p>
      </div>

      {papers.length === 0 ? (
        <div className="text-center py-16 text-[var(--muted-foreground)]">
          <p className="text-4xl mb-4">📭</p>
          <p>暂无论文数据</p>
          <p className="text-sm mt-2">请先运行数据导入脚本：<code>python scripts/import_to_supabase.py</code></p>
        </div>
      ) : (
        <div className="space-y-4">
          {papers.map((paper) => (
            <Link
              key={paper.id}
              href={`/papers/${paper.slug}`}
              className="block no-underline"
            >
              <div className="border border-[var(--border)] rounded-lg p-5 hover:border-[var(--primary)] hover:shadow-md transition-all">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <h2 className="font-semibold text-base leading-snug mb-1 text-[var(--foreground)]">
                      {paper.title || paper.slug}
                    </h2>
                    <div className="flex items-center gap-3 text-sm text-[var(--muted-foreground)]">
                      {paper.journal && <span>{paper.journal}</span>}
                      {paper.doi && (
                        <span className="truncate max-w-[200px]">DOI: {paper.doi}</span>
                      )}
                    </div>
                    <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
                      <span className="inline-flex items-center rounded px-2 py-0.5 bg-[var(--muted)] text-[var(--muted-foreground)] font-mono break-all">
                        slug: {paper.slug}
                      </span>
                      <span
                        className={`inline-flex items-center rounded px-2 py-0.5 ${paper.slug.startsWith('mineru_') || paper.slug === 'full' || paper.slug === 'full-1' || paper.slug === 'new'
                          ? 'bg-orange-100 text-orange-800'
                          : 'bg-green-100 text-green-800'
                        }`}
                      >
                        {paper.slug.startsWith('mineru_') || paper.slug === 'full' || paper.slug === 'full-1' || paper.slug === 'new'
                          ? '旧数据'
                          : '新导入数据'}
                      </span>
                    </div>
                  </div>
                  <StatusBadge status={paper.status} />
                </div>

                <div className="flex items-center gap-4 mt-3 text-sm">
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[var(--muted)] text-[var(--muted-foreground)]">
                    🧬 {paper.gene_count} 个基因
                  </span>
                </div>

                <VerificationBar summary={paper.verification_report} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
