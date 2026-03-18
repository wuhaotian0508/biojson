'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Paper, Gene, Annotation, FieldVerdict, GeneData } from '@/lib/types'
import { GENE_FIELD_GROUPS, FIELD_LABELS } from '@/lib/types'
import { supabase } from '@/lib/supabase'

interface Props {
  paper: Paper
  genes: Gene[]
  annotations: Annotation[]
}

// ─── 验证徽章 ──────────────────────────────────────────────
function VerdictBadge({ verdict }: { verdict: string }) {
  const cfg: Record<string, { label: string; cls: string }> = {
    SUPPORTED:   { label: '✅ 支持', cls: 'bg-green-100 text-green-800' },
    UNSUPPORTED: { label: '❌ 不支持', cls: 'bg-red-100 text-red-800' },
    UNCERTAIN:   { label: '❓ 不确定', cls: 'bg-yellow-100 text-yellow-800' },
  }
  const c = cfg[verdict] || { label: verdict, cls: 'bg-gray-100 text-gray-800' }
  return <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${c.cls}`}>{c.label}</span>
}

// ─── 专家标注徽章 ──────────────────────────────────────────
function AnnotationBadge({ verdict }: { verdict: string }) {
  const cfg: Record<string, { label: string; cls: string }> = {
    correct:   { label: '✅ 正确', cls: 'bg-green-100 text-green-800' },
    incorrect: { label: '❌ 错误', cls: 'bg-red-100 text-red-800' },
    modified:  { label: '✏️ 已修改', cls: 'bg-blue-100 text-blue-800' },
  }
  const c = cfg[verdict] || { label: verdict, cls: 'bg-gray-100' }
  return <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${c.cls}`}>{c.label}</span>
}

// ─── 单个字段行 ────────────────────────────────────────────
function FieldRow({
  fieldName,
  value,
  autoVerdict,
  annotation,
  geneId,
  onAnnotationChange,
}: {
  fieldName: string
  value: string | string[] | undefined
  autoVerdict?: FieldVerdict
  annotation?: Annotation
  geneId: string
  onAnnotationChange: () => void
}) {
  const [showForm, setShowForm] = useState(false)
  const [comment, setComment] = useState(annotation?.comment || '')
  const [correctedValue, setCorrectedValue] = useState(annotation?.corrected_value || '')
  const [saving, setSaving] = useState(false)

  const displayValue = Array.isArray(value) ? value.join(', ') : (value || 'NA')
  const isNA = displayValue === 'NA' || displayValue.trim() === ''
  const label = FIELD_LABELS[fieldName] || fieldName

  async function saveAnnotation(verdict: 'correct' | 'incorrect' | 'modified') {
    setSaving(true)
    try {
      const payload = {
        gene_id: geneId,
        field_name: fieldName,
        expert_verdict: verdict,
        corrected_value: verdict === 'modified' ? correctedValue : null,
        comment: comment || null,
        annotator_id: null, // 无认证时为 null
      }

      if (annotation) {
        // @ts-expect-error - Supabase has no generated types for our custom tables
        await supabase.from('annotations').update(payload).eq('id', annotation.id)
      } else {
        // @ts-expect-error - Supabase has no generated types for our custom tables
        await supabase.from('annotations').insert(payload)
      }
      onAnnotationChange()
      setShowForm(false)
    } catch (e) {
      console.error('Save annotation failed:', e)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={`py-2 px-3 border-b border-[var(--border)] last:border-b-0 ${isNA ? 'opacity-50' : ''}`}>
      {/* 字段名 + 值 */}
      <div className="flex items-start gap-2 mb-1">
        <span className="text-xs font-medium text-[var(--muted-foreground)] min-w-[100px] shrink-0 pt-0.5">
          {label}
        </span>
        <span className="text-sm flex-1 break-words">{displayValue}</span>
      </div>

      {/* 自动验证 + 专家标注 */}
      <div className="flex items-center gap-2 ml-[100px] flex-wrap">
        {autoVerdict && <VerdictBadge verdict={autoVerdict.verdict} />}
        {annotation && <AnnotationBadge verdict={annotation.expert_verdict} />}
        {!isNA && (
          <button
            onClick={() => setShowForm(!showForm)}
            className="text-xs text-[var(--primary)] hover:underline cursor-pointer"
          >
            {annotation ? '修改标注' : '标注'}
          </button>
        )}
      </div>

      {/* 自动验证理由 */}
      {autoVerdict?.reason && (
        <p className="text-xs text-[var(--muted-foreground)] ml-[100px] mt-1 italic">
          AI: {autoVerdict.reason.length > 120 ? autoVerdict.reason.slice(0, 120) + '...' : autoVerdict.reason}
        </p>
      )}

      {/* 标注表单 */}
      {showForm && (
        <div className="ml-[100px] mt-2 p-3 bg-[var(--muted)] rounded-lg space-y-2">
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="评论/理由（可选）"
            className="w-full text-sm p-2 rounded border border-[var(--border)] bg-[var(--background)] resize-none"
            rows={2}
          />
          <input
            value={correctedValue}
            onChange={(e) => setCorrectedValue(e.target.value)}
            placeholder="修正值（仅当选择「修改」时填写）"
            className="w-full text-sm p-2 rounded border border-[var(--border)] bg-[var(--background)]"
          />
          <div className="flex gap-2">
            <button
              onClick={() => saveAnnotation('correct')}
              disabled={saving}
              className="px-3 py-1 text-xs rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 cursor-pointer"
            >
              ✅ 正确
            </button>
            <button
              onClick={() => saveAnnotation('incorrect')}
              disabled={saving}
              className="px-3 py-1 text-xs rounded bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 cursor-pointer"
            >
              ❌ 错误
            </button>
            <button
              onClick={() => saveAnnotation('modified')}
              disabled={saving || !correctedValue}
              className="px-3 py-1 text-xs rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
            >
              ✏️ 修改
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-3 py-1 text-xs rounded bg-[var(--muted)] border border-[var(--border)] hover:bg-[var(--border)] cursor-pointer"
            >
              取消
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── 基因卡片 ──────────────────────────────────────────────
function GeneCard({
  gene,
  annotations,
  onAnnotationChange,
}: {
  gene: Gene
  annotations: Annotation[]
  onAnnotationChange: () => void
}) {
  const [expanded, setExpanded] = useState(true)
  const geneData = gene.gene_data as GeneData
  const autoVerification = (gene.auto_verification || {}) as Record<string, FieldVerdict>
  const stats = gene.auto_stats as { supported: number; unsupported: number; uncertain: number } | null

  return (
    <div className="border border-[var(--border)] rounded-lg overflow-hidden mb-4">
      {/* 基因头部 */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 bg-[var(--muted)] flex items-center justify-between cursor-pointer hover:bg-[var(--border)] transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold">🧬 {gene.gene_name || `Gene ${gene.gene_index}`}</span>
          {stats && (
            <span className="text-xs text-[var(--muted-foreground)]">
              ✅{stats.supported} ❓{stats.uncertain} ❌{stats.unsupported}
            </span>
          )}
          <span className="text-xs text-[var(--muted-foreground)]">
            📝 {annotations.length} 条标注
          </span>
        </div>
        <span className="text-[var(--muted-foreground)]">{expanded ? '▼' : '▶'}</span>
      </button>

      {/* 字段列表 */}
      {expanded && (
        <div>
          {GENE_FIELD_GROUPS.map((group) => {
            const visibleFields = group.fields.filter((f) => {
              const val = geneData[f]
              return val !== undefined
            })
            if (visibleFields.length === 0) return null

            return (
              <div key={group.label}>
                <div className="px-4 py-1.5 bg-[var(--muted)] text-xs font-semibold text-[var(--muted-foreground)] uppercase tracking-wide border-t border-[var(--border)]">
                  {group.label}
                </div>
                {visibleFields.map((fieldName) => (
                  <FieldRow
                    key={fieldName}
                    fieldName={fieldName}
                    value={geneData[fieldName]}
                    autoVerdict={autoVerification[fieldName]}
                    annotation={annotations.find((a) => a.field_name === fieldName)}
                    geneId={gene.id}
                    onAnnotationChange={onAnnotationChange}
                  />
                ))}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ─── 主组件 ────────────────────────────────────────────────
export default function PaperDetail({ paper, genes, annotations: initialAnnotations }: Props) {
  const [annotations, setAnnotations] = useState(initialAnnotations)
  const [activeGeneIdx, setActiveGeneIdx] = useState(0)

  // 刷新标注
  async function refreshAnnotations() {
    const geneIds = genes.map((g) => g.id)
    if (geneIds.length === 0) return
    const { data } = await supabase
      .from('annotations')
      .select('*')
      .in('gene_id', geneIds)
    if (data) setAnnotations(data as Annotation[])
  }

  return (
    <div className="flex h-[calc(100vh-3.5rem)]">
      {/* ── 左侧：MD 原文 ──────────────────────── */}
      <div className="w-1/2 border-r border-[var(--border)] overflow-y-auto">
        <div className="p-6">
          <div className="mb-4 pb-3 border-b border-[var(--border)]">
            <h1 className="text-lg font-bold mb-1">{paper.title || paper.slug}</h1>
            <div className="flex gap-3 text-sm text-[var(--muted-foreground)]">
              {paper.journal && <span>{paper.journal}</span>}
              {paper.doi && <span>DOI: {paper.doi}</span>}
            </div>
          </div>
          <div className="markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {paper.md_content}
            </ReactMarkdown>
          </div>
        </div>
      </div>

      {/* ── 右侧：基因卡片 + 标注 ──────────────── */}
      <div className="w-1/2 overflow-y-auto">
        <div className="p-4">
          {/* 基因切换标签 */}
          {genes.length > 1 && (
            <div className="flex gap-1 mb-4 overflow-x-auto pb-1">
              {genes.map((gene, idx) => (
                <button
                  key={gene.id}
                  onClick={() => setActiveGeneIdx(idx)}
                  className={`px-3 py-1.5 text-sm rounded-full whitespace-nowrap cursor-pointer transition-colors ${
                    idx === activeGeneIdx
                      ? 'bg-[var(--primary)] text-[var(--primary-foreground)]'
                      : 'bg-[var(--muted)] text-[var(--muted-foreground)] hover:bg-[var(--border)]'
                  }`}
                >
                  {gene.gene_name || `Gene ${gene.gene_index}`}
                </button>
              ))}
            </div>
          )}

          {genes.length === 0 ? (
            <div className="text-center py-16 text-[var(--muted-foreground)]">
              <p className="text-4xl mb-4">🔬</p>
              <p>此论文暂无提取的基因数据</p>
            </div>
          ) : (
            <GeneCard
              gene={genes[activeGeneIdx]}
              annotations={annotations.filter((a) => a.gene_id === genes[activeGeneIdx].id)}
              onAnnotationChange={refreshAnnotations}
            />
          )}
        </div>
      </div>
    </div>
  )
}
