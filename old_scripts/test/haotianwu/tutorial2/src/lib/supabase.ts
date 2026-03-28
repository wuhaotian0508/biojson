/**
 * supabase.ts - Supabase 客户端配置
 *
 * 这是 TypeScript 文件 (.ts)
 * 功能：创建一个可以在整个应用中使用的 Supabase 客户端
 */

import { createClient } from '@supabase/supabase-js'

// 从环境变量读取配置
const supabaseUrl = process.env.SUPABASE_URL || ''
const supabaseAnonKey = process.env.SUPABASE_ANON_KEY || ''

// 创建并导出客户端
export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// 类型定义：论文数据结构
export interface Paper {
  id: string
  slug: string
  title: string | null
  journal: string | null
  doi: string | null
  gene_count: number
  status: string
  created_at: string
}

// 类型定义：基因数据结构
export interface Gene {
  id: string
  paper_id: string
  gene_index: number
  gene_name: string | null
  gene_data: Record<string, any>
}
