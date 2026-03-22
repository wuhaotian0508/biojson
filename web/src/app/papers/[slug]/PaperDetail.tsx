'use client'

import { useState, useCallback, useEffect, useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Paper, Gene, Annotation, FieldVerdict, GeneData, VerificationReport } from '@/lib/types'
import { FIELD_LABELS, FIELD_ORDER } from '@/lib/types'
import { supabase } from '@/lib/supabase'
import { useUser } from '@/lib/UserContext'

interface Props {
  paper: Paper
  genes: Gene[]
  annotations: Annotation[]
}

function getAnnotationOwnerLabel(annotation?: Annotation) {
  if (!annotation) return null
  return annotation.annotator_name || annotation.annotator_id || '未知用户'
}

function getUserAnnotation(annotations: Annotation[], fieldName: string, username: string | null) {
  if (annotations.length === 0) return undefined
  if (username) {
    const matched = annotations.find((a) => a.field_name === fieldName && a.annotator_name === username)
    if (matched) return matched
  }
  return annotations.find((a) => a.field_name === fieldName)
}

function getOtherAnnotations(annotations: Annotation[], fieldName: string, username: string | null) {
  return annotations.filter((a) => a.field_name === fieldName && (!username || a.annotator_name !== username))
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

// ─── 可展开文本（用于 AI 长批注）────────────────────────────
function ExpandableText({ text, maxLen = 120, className = '' }: { text: string; maxLen?: number; className?: string }) {
  const [expanded, setExpanded] = useState(false)
  if (text.length <= maxLen) {
    return <span className={className}>{text}</span>
  }
  return (
    <span className={className}>
      {expanded ? text : text.slice(0, maxLen) + '...'}
      <button
        onClick={() => setExpanded(!expanded)}
        className="ml-1 text-[var(--primary)] hover:underline cursor-pointer font-medium"
      >
        {expanded ? '收起' : '展开'}
      </button>
    </span>
  )
}

// ─── 基因级别下拉框（应该提取 / 不应该提取 / 尚未评分）────────
function GeneVerdictSelect({
  value,
  onChange,
  disabled,
}: {
  value: string
  onChange: (v: string) => void
  disabled?: boolean
}) {
  const colorMap: Record<string, string> = {
    unrated: 'border-gray-300 bg-gray-50 text-gray-500',
    should_extract: 'border-green-400 bg-green-50 text-green-700',
    should_not_extract: 'border-red-400 bg-red-50 text-red-700',
  }
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className={`text-xs px-2 py-1 rounded border cursor-pointer disabled:opacity-50 ${colorMap[value] || colorMap.unrated}`}
    >
      <option value="unrated">尚未评分</option>
      <option value="should_extract">应该提取</option>
      <option value="should_not_extract">不应该提取</option>
    </select>
  )
}

// ─── 字段级别下拉框（好 / 中 / 差 / 尚未评分）────────────────
function FieldVerdictSelect({
  value,
  onChange,
  disabled,
}: {
  value: string
  onChange: (v: string) => void
  disabled?: boolean
}) {
  const colorMap: Record<string, string> = {
    unrated: 'border-gray-300 bg-gray-50 text-gray-500',
    good: 'border-green-400 bg-green-50 text-green-700',
    medium: 'border-yellow-400 bg-yellow-50 text-yellow-700',
    poor: 'border-red-400 bg-red-50 text-red-700',
  }
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className={`text-xs px-2 py-1 rounded border cursor-pointer disabled:opacity-50 ${colorMap[value] || colorMap.unrated}`}
    >
      <option value="unrated">尚未评分</option>
      <option value="good">好</option>
      <option value="medium">中</option>
      <option value="poor">差</option>
    </select>
  )
}

// ─── Metadata 标注行 ───────────────────────────────────────
function MetadataRow({
  label,
  value,
  fieldName,
  annotation,
  onSave,
  disabled,
}: {
  label: string
  value: string | null
  fieldName: string
  annotation?: { verdict: string; comment: string }
  onSave: (fieldName: string, verdict: string, comment: string) => void
  disabled?: boolean
}) {
  const [comment, setComment] = useState(annotation?.comment || '')

  return (
    <div className="py-3 border-b border-[var(--border)] last:border-b-0">
      <div className="flex items-center gap-2 mb-1">
        <span className="font-semibold text-sm min-w-[70px]">{label}</span>
        <FieldVerdictSelect
          value={annotation?.verdict || 'unrated'}
          onChange={(v) => onSave(fieldName, v, comment)}
          disabled={disabled}
        />
      </div>
      <div className="ml-0 mt-1 px-3 py-2 bg-[var(--muted)] rounded text-sm break-words">
        {value || <span className="text-[var(--muted-foreground)] italic">未提取</span>}
      </div>
      <textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        onBlur={() => {
          if (annotation?.verdict) onSave(fieldName, annotation.verdict, comment)
        }}
        placeholder="Add comment..."
        className="mt-1 w-full text-xs p-2 rounded border border-[var(--border)] bg-[var(--background)] resize-none"
        rows={1}
      />
    </div>
  )
}

// ─── 单个字段行 ────────────────────────────────────────────
function FieldRow({
  fieldName,
  value,
  autoVerdict,
  annotation,
  otherAnnotations,
  geneId,
  onAnnotationChange,
  username,
}: {
  fieldName: string
  value: string | string[] | undefined
  autoVerdict?: FieldVerdict
  annotation?: Annotation
  otherAnnotations?: Annotation[]
  geneId: string
  onAnnotationChange: () => void
  username: string | null
}) {
  const [comment, setComment] = useState(annotation?.comment || '')
  const [correctedValue, setCorrectedValue] = useState(annotation?.corrected_value || '')
  const [saving, setSaving] = useState(false)
  const [fieldVerdict, setFieldVerdict] = useState<string>(annotation?.expert_verdict || 'unrated')

  const raw = Array.isArray(value) ? value.join(', ') : (value ?? '')
  const displayValue = String(raw)
  const isNA = !displayValue || displayValue.trim() === '' || displayValue === 'NA'
  const label = FIELD_LABELS[fieldName] || fieldName

  async function saveAnnotation(verdict: string) {
    if (!username) {
      alert('请先登录再标注')
      return
    }
    if (verdict === 'unrated') return
    setSaving(true)
    try {
      const payload = {
        gene_id: geneId,
        field_name: fieldName,
        expert_verdict: verdict,
        corrected_value: correctedValue || null,
        comment: comment || null,
        annotator_id: null,
        annotator_name: username,
      }

      if (annotation) {
        // @ts-expect-error - Supabase has no generated types for our custom tables
        await supabase.from('annotations').update(payload).eq('id', annotation.id)
      } else {
        // @ts-expect-error - Supabase has no generated types for our custom tables
        await supabase.from('annotations').insert(payload)
      }
      onAnnotationChange()
    } catch (e) {
      console.error('Save annotation failed:', e)
    } finally {
      setSaving(false)
    }
  }

  function handleVerdictChange(v: string) {
    setFieldVerdict(v)
    saveAnnotation(v)
  }

  return (
    <div className={`py-2 px-3 border-b border-[var(--border)] last:border-b-0`}>
      {/* 字段名 + 值 + 评分下拉框 */}
      <div className="flex items-start gap-2 mb-1">
        <span className="text-xs font-medium text-[var(--muted-foreground)] min-w-[100px] shrink-0 pt-0.5">
          {label}
        </span>
        <span className={`text-sm flex-1 break-words ${isNA ? 'text-[var(--muted-foreground)] italic' : ''}`}>
          {displayValue}
        </span>
        <FieldVerdictSelect
          value={fieldVerdict}
          onChange={handleVerdictChange}
          disabled={!username || saving}
        />
      </div>

      {/* 自动验证 + 其他标注人信息 */}
      <div className="flex items-center gap-2 ml-[100px] flex-wrap">
        {autoVerdict && <VerdictBadge verdict={autoVerdict.verdict} />}
        {annotation && (
          <span className="text-xs text-[var(--muted-foreground)]">
            当前标注人：{getAnnotationOwnerLabel(annotation)}
          </span>
        )}
      </div>

      {/* 自动验证理由 */}
      {autoVerdict?.reason && (
        <p className="text-xs text-[var(--muted-foreground)] ml-[100px] mt-1 italic">
          AI: <ExpandableText text={autoVerdict.reason} maxLen={150} />
        </p>
      )}

      {!!otherAnnotations?.length && (
        <div className="ml-[100px] mt-1 flex flex-wrap gap-1.5">
          {otherAnnotations.map((item) => (
            <span
              key={item.id}
              className="text-xs px-2 py-0.5 rounded bg-[var(--muted)] text-[var(--muted-foreground)] border border-[var(--border)]"
              title={item.comment || undefined}
            >
              {getAnnotationOwnerLabel(item)}：{item.expert_verdict}
            </span>
          ))}
        </div>
      )}

      {/* 评论 + 修正值（始终可见） */}
      <div className="ml-[100px] mt-1.5 space-y-1">
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          onBlur={() => { if (fieldVerdict !== 'unrated') saveAnnotation(fieldVerdict) }}
          placeholder="评论/理由（可选）"
          className="w-full text-xs p-1.5 rounded border border-[var(--border)] bg-[var(--background)] resize-none"
          rows={1}
          disabled={!username}
        />
        <input
          value={correctedValue}
          onChange={(e) => setCorrectedValue(e.target.value)}
          onBlur={() => { if (fieldVerdict !== 'unrated') saveAnnotation(fieldVerdict) }}
          placeholder="修正值（可选）"
          className="w-full text-xs p-1.5 rounded border border-[var(--border)] bg-[var(--background)]"
          disabled={!username}
        />
      </div>
    </div>
  )
}

// ─── 基因卡片 ──────────────────────────────────────────────
function GeneCard({
  gene,
  geneVerification,
  annotations,
  onAnnotationChange,
  username,
}: {
  gene: Gene
  geneVerification?: { verdict: string; reason: string }
  annotations: Annotation[]
  onAnnotationChange: () => void
  username: string | null
}) {
  const [expanded, setExpanded] = useState(true)
  const [geneVerdict, setGeneVerdict] = useState<string | undefined>(undefined)
  const geneData = ((gene?.gene_data || {}) as GeneData)
  const autoVerification = (gene.auto_verification || {}) as Record<string, FieldVerdict>
  const stats = gene.auto_stats as { supported: number; unsupported: number; uncertain: number } | null

  // 按 FIELD_ORDER 排序字段，未在 FIELD_ORDER 中的字段追加到末尾
  const dataKeys = new Set(Object.keys(geneData))
  const orderedFields = FIELD_ORDER.filter((f) => dataKeys.has(f))
  // 追加 FIELD_ORDER 中没有但 geneData 中存在的字段
  for (const k of dataKeys) {
    if (!orderedFields.includes(k)) orderedFields.push(k)
  }
  const allFields = orderedFields

  return (
    <div className="border border-[var(--border)] rounded-lg overflow-hidden mb-4">
      {/* 基因头部 */}
      <div className="px-4 py-3 bg-[var(--muted)] flex items-center justify-between">
        <div className="flex items-center gap-3 flex-wrap">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-lg font-semibold cursor-pointer hover:opacity-80"
          >
            🧬 {gene.gene_name || `Gene ${gene.gene_index}`}
            <span className="text-[var(--muted-foreground)] ml-2">{expanded ? '▼' : '▶'}</span>
          </button>
          {/* 基因整体级别标注下拉框 */}
          <GeneVerdictSelect
            value={geneVerdict || 'unrated'}
            onChange={(v) => setGeneVerdict(v)}
            disabled={!username}
          />
          {stats && (
            <span className="text-xs text-[var(--muted-foreground)]">
              ✅{stats.supported} ❓{stats.uncertain} ❌{stats.unsupported}
            </span>
          )}
          <span className="text-xs text-[var(--muted-foreground)]">
            📝 {annotations.length} 条标注
          </span>
        </div>
      </div>

      {/* 基因级别 Verification 信息 */}
      {geneVerification && (
        <div className="px-4 py-2 bg-blue-50 dark:bg-blue-950 border-b border-[var(--border)]">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold text-blue-700 dark:text-blue-300">AI 验证结果:</span>
            <VerdictBadge verdict={geneVerification.verdict} />
          </div>
          <p className="text-xs text-blue-600 dark:text-blue-400 leading-relaxed">
            <ExpandableText text={geneVerification.reason} maxLen={200} />
          </p>
        </div>
      )}

      {/* 字段列表（平铺，不分组） */}
      {expanded && (
        <div>
          {allFields.map((fieldName) => {
            const val = geneData[fieldName]
            const strVal = String(Array.isArray(val) ? val.join(', ') : (val ?? ''))
            // 跳过空值字段
            if (!strVal || strVal.trim() === '' || strVal === 'NA') return null
            const currentAnnotation = getUserAnnotation(annotations, fieldName, username)
            const others = getOtherAnnotations(annotations, fieldName, username)
            return (
              <FieldRow
                key={fieldName}
                fieldName={fieldName}
                value={val}
                autoVerdict={autoVerification[fieldName]}
                annotation={currentAnnotation}
                otherAnnotations={others}
                geneId={gene.id}
                onAnnotationChange={onAnnotationChange}
                username={username}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}

// ─── Gene Categories 区域 ──────────────────────────────────
function GeneCategoriesSection({
  paper,
  genes,
  username,
}: {
  paper: Paper
  genes: Gene[]
  username: string | null
}) {
  // 从 extraction_json 检查是否有分类结构
  const json = paper.extraction_json || {}
  const inner = json.CropNutrientMetabolismGeneExtraction || json
  
  // 尝试检测类别（v2 schema 用 Pathway_Genes / Regulation_Genes / Common_Genes）
  const categories: { key: string; label: string; genes: string[] }[] = []
  
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const rawJson = inner as any
  
  if (rawJson.Pathway_Genes && Array.isArray(rawJson.Pathway_Genes)) {
    categories.push({
      key: 'Pathway_Genes',
      label: 'Pathway_Genes',
      genes: rawJson.Pathway_Genes.map((g: GeneData) => g.Gene_Name || 'NA'),
    })
  }
  if (rawJson.Regulation_Genes && Array.isArray(rawJson.Regulation_Genes)) {
    categories.push({
      key: 'Regulation_Genes',
      label: 'Regulation_Genes',
      genes: rawJson.Regulation_Genes.map((g: GeneData) => g.Gene_Name || 'NA'),
    })
  }
  if (rawJson.Common_Genes && Array.isArray(rawJson.Common_Genes)) {
    categories.push({
      key: 'Common_Genes',
      label: 'Common_Genes',
      genes: rawJson.Common_Genes.map((g: GeneData) => g.Gene_Name || 'NA'),
    })
  }
  
  // 如果没有分类结构，使用默认 Genes
  if (categories.length === 0 && genes.length > 0) {
    categories.push({
      key: 'Genes',
      label: 'Genes',
      genes: genes.map((g) => g.gene_name || 'NA'),
    })
  }

  const [missingReasons, setMissingReasons] = useState<Record<string, string>>({})

  if (categories.length === 0) return null

  return (
    <div className="border border-[var(--border)] rounded-lg p-4 mb-4">
      <h3 className="text-base font-semibold mb-3">Gene Categories</h3>
      {categories.map((cat) => (
        <div key={cat.key} className="mb-3 last:mb-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`px-3 py-1 text-xs rounded font-medium ${
              cat.key === 'Pathway_Genes' ? 'bg-green-100 text-green-800 border border-green-300' :
              cat.key === 'Regulation_Genes' ? 'bg-purple-100 text-purple-800 border border-purple-300' :
              cat.key === 'Common_Genes' ? 'bg-blue-100 text-blue-800 border border-blue-300' :
              'bg-gray-100 text-gray-800 border border-gray-300'
            }`}>
              {cat.label}
            </span>
            <span className="text-xs text-[var(--muted-foreground)]">
              ({cat.genes.length} genes: {cat.genes.join(', ')})
            </span>
          </div>
          <div className="mt-1 flex items-center gap-2">
            <span className="text-xs text-[var(--muted-foreground)] shrink-0">missing genes with reasons:</span>
            <input
              value={missingReasons[cat.key] || ''}
              onChange={(e) => setMissingReasons({ ...missingReasons, [cat.key]: e.target.value })}
              placeholder="如有遗漏的基因，请说明..."
              className="flex-1 text-xs p-1.5 rounded border border-[var(--border)] bg-[var(--background)]"
              disabled={!username}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

// ─── 主组件 ────────────────────────────────────────────────
export default function PaperDetail({ paper, genes, annotations: initialAnnotations }: Props) {
  const { username } = useUser()
  const [annotations, setAnnotations] = useState(initialAnnotations)
  const [activeGeneId, setActiveGeneId] = useState<string | null>(genes[0]?.id ?? null)
  const [saving, setSaving] = useState(false)
  const [saveMessage, setSaveMessage] = useState('')

  // Metadata 标注状态
  const [metaAnnotations, setMetaAnnotations] = useState<Record<string, { verdict: string; comment: string }>>({})

  // 从 verification_report 中获取基因级别验证信息
  const verificationReport = paper.verification_report as VerificationReport | null
  const geneVerifications: Record<number, { verdict: string; reason: string }> = {}
  if (verificationReport?.genes) {
    for (const vg of verificationReport.genes) {
      // verification key 可能是空字符串 "" 或字段名
      const verificationEntries = Object.entries(vg.verification || {})
      if (verificationEntries.length > 0) {
        // 取第一个验证条目（通常 key 是空字符串代表基因级别）
        const [, firstVerdict] = verificationEntries[0]
        geneVerifications[vg.gene_index] = {
          verdict: firstVerdict.verdict,
          reason: firstVerdict.reason,
        }
      }
    }
  }

  useEffect(() => {
    if (genes.length === 0) {
      setActiveGeneId(null)
      return
    }
    const activeExists = activeGeneId && genes.some((gene) => gene.id === activeGeneId)
    if (!activeExists) {
      setActiveGeneId(genes[0].id)
    }
  }, [activeGeneId, genes])

  const activeGene = useMemo(() => {
    if (genes.length === 0) return null
    return genes.find((gene) => gene.id === activeGeneId) || genes[0]
  }, [activeGeneId, genes])

  const activeGeneAnnotations = useMemo(() => {
    if (!activeGene) return []
    return annotations.filter((a) => a.gene_id === activeGene.id)
  }, [activeGene, annotations])

  // 刷新标注
  const refreshAnnotations = useCallback(async () => {
    const geneIds = genes.map((g) => g.id)
    if (geneIds.length === 0) return
    const { data } = await supabase
      .from('annotations')
      .select('*')
      .in('gene_id', geneIds)
    if (data) setAnnotations(data as Annotation[])
  }, [genes])

  // 保存 metadata 标注
  function handleMetaSave(fieldName: string, verdict: string, comment: string) {
    if (!username) {
      alert('请先登录再标注')
      return
    }
    setMetaAnnotations((prev) => ({
      ...prev,
      [fieldName]: { verdict, comment },
    }))
  }

  // 全局保存
  async function handleGlobalSave() {
    if (!username) {
      alert('请先登录再保存')
      return
    }
    setSaving(true)
    setSaveMessage('')
    try {
      // 目前已保存的标注是通过 FieldRow 内的即时保存完成的
      // 这里可以做额外的批量保存或状态更新
      // 更新论文状态为 in_review
      // @ts-expect-error - Supabase has no generated types
      await supabase.from('papers').update({ status: 'in_review' }).eq('id', paper.id)
      setSaveMessage('✅ 保存成功！')
      setTimeout(() => setSaveMessage(''), 3000)
    } catch (e) {
      console.error('Save failed:', e)
      setSaveMessage('❌ 保存失败')
    } finally {
      setSaving(false)
    }
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

      {/* ── 右侧：标注区域 ──────────────── */}
      <div className="w-1/2 overflow-y-auto">
        <div className="p-4">
          {/* Save 按钮 */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold">标注面板</h2>
            <div className="flex items-center gap-2">
              {saveMessage && (
                <span className="text-sm">{saveMessage}</span>
              )}
              <button
                onClick={handleGlobalSave}
                disabled={saving || !username}
                className="px-4 py-2 text-sm rounded bg-red-500 text-white hover:bg-red-600 disabled:opacity-50 cursor-pointer font-medium"
              >
                {saving ? '保存中...' : 'Save'}
              </button>
            </div>
          </div>

          {/* Metadata 标注区域 */}
          <div className="border border-[var(--border)] rounded-lg p-4 mb-4">
            <h3 className="text-base font-semibold mb-2">Metadata</h3>
            <MetadataRow
              label="Title"
              value={paper.title}
              fieldName="meta_title"
              annotation={metaAnnotations['meta_title']}
              onSave={handleMetaSave}
              disabled={!username}
            />
            <MetadataRow
              label="Journal"
              value={paper.journal}
              fieldName="meta_journal"
              annotation={metaAnnotations['meta_journal']}
              onSave={handleMetaSave}
              disabled={!username}
            />
            <MetadataRow
              label="DOI"
              value={paper.doi}
              fieldName="meta_doi"
              annotation={metaAnnotations['meta_doi']}
              onSave={handleMetaSave}
              disabled={!username}
            />
          </div>

          {/* Gene Categories 区域 */}
          <GeneCategoriesSection
            paper={paper}
            genes={genes}
            username={username}
          />

          {/* 基因切换标签 */}
          {genes.length > 1 && (
            <div className="flex gap-1 mb-4 overflow-x-auto pb-1">
              {genes.map((gene) => (
                <button
                  key={gene.id}
                  onClick={() => setActiveGeneId(gene.id)}
                  className={`px-3 py-1.5 text-sm rounded-full whitespace-nowrap cursor-pointer transition-colors ${
                    gene.id === activeGene?.id
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
          ) : activeGene ? (
            <GeneCard
              gene={activeGene}
              geneVerification={geneVerifications[activeGene.gene_index] || geneVerifications[activeGene.gene_index + 1]}
              annotations={activeGeneAnnotations}
              onAnnotationChange={refreshAnnotations}
              username={username}
            />
          ) : (
            <div className="text-center py-16 text-[var(--muted-foreground)]">
              <p>当前基因信息不可用，请重新选择。</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
