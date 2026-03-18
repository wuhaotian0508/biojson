import { supabase } from '@/lib/supabase'
import { notFound } from 'next/navigation'
import type { Paper, Gene, Annotation } from '@/lib/types'
import PaperDetail from './PaperDetail'

export const revalidate = 30

interface Props {
  params: Promise<{ slug: string }>
}

async function getPaper(slug: string): Promise<Paper | null> {
  const { data, error } = await supabase
    .from('papers')
    .select('*')
    .eq('slug', slug)
    .single()

  if (error || !data) return null
  return data as Paper
}

async function getGenes(paperId: string): Promise<Gene[]> {
  const { data, error } = await supabase
    .from('genes')
    .select('*')
    .eq('paper_id', paperId)
    .order('gene_index', { ascending: true })

  if (error) return []
  return (data || []) as Gene[]
}

async function getAnnotations(geneIds: string[]): Promise<Annotation[]> {
  if (geneIds.length === 0) return []
  const { data, error } = await supabase
    .from('annotations')
    .select('*')
    .in('gene_id', geneIds)

  if (error) return []
  return (data || []) as Annotation[]
}

export default async function PaperPage({ params }: Props) {
  const { slug } = await params
  const paper = await getPaper(slug)
  if (!paper) notFound()

  const genes = await getGenes(paper.id)
  const geneIds = genes.map((g) => g.id)
  const annotations = await getAnnotations(geneIds)

  return <PaperDetail paper={paper} genes={genes} annotations={annotations} />
}
