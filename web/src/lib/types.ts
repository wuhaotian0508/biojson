// ═══════════════════════════════════════════════════════════
// BioJSON Web Platform - TypeScript 类型定义
// ═══════════════════════════════════════════════════════════

// Supabase Database 类型
export interface Database {
  public: {
    Tables: {
      papers: {
        Row: Paper
        Insert: Omit<Paper, 'id' | 'created_at' | 'updated_at'>
        Update: Partial<Omit<Paper, 'id'>>
      }
      genes: {
        Row: Gene
        Insert: Omit<Gene, 'id' | 'created_at'>
        Update: Partial<Omit<Gene, 'id'>>
      }
      annotations: {
        Row: Annotation
        Insert: Omit<Annotation, 'id' | 'created_at' | 'updated_at'>
        Update: Partial<Omit<Annotation, 'id'>>
      }
    }
    Views: Record<string, never>
    Functions: Record<string, never>
    Enums: Record<string, never>
  }
}

// 论文
export interface Paper {
  id: string
  slug: string
  title: string | null
  journal: string | null
  doi: string | null
  md_content: string
  extraction_json: ExtractionJSON
  verified_json: ExtractionJSON | null
  verification_report: VerificationReport | null
  gene_count: number
  status: 'pending' | 'in_review' | 'completed'
  created_at: string
  updated_at: string
}

// 基因
export interface Gene {
  id: string
  paper_id: string
  gene_index: number
  gene_name: string | null
  gene_data: GeneData
  auto_verification: Record<string, FieldVerdict> | null
  auto_stats: VerificationStats | null
  created_at: string
}

// 基因 + 标注（用于前端展示）
export interface GeneWithAnnotations extends Gene {
  annotations: Annotation[]
}

// 标注
export interface Annotation {
  id: string
  gene_id: string
  field_name: string
  expert_verdict: 'good' | 'medium' | 'poor' | 'unrated' | 'should_extract' | 'should_not_extract' | 'correct' | 'incorrect' | 'modified'
  corrected_value: string | null
  comment: string | null
  annotator_id: string | null
  annotator_name: string | null
  created_at: string
  updated_at: string
}

// 提取结果 JSON 结构
export interface ExtractionJSON {
  Title?: string
  Journal?: string
  DOI?: string
  Genes?: GeneData[]
  CropNutrientMetabolismGeneExtraction?: {
    Title?: string
    Journal?: string
    DOI?: string
    Genes?: GeneData[]
  }
}

// 单个基因的字段（v2 schema - 45 个字段，与 nutri_fields_v2.xlsx 一致）
export interface GeneData {
  // ── 通用 - 物种相关 ──
  'Species_Common Name'?: string
  Species_Latin_Name?: string
  Variety_or_Cultivar?: string
  // ── 通用 - 基因相关 ──
  Gene_Name?: string
  Gene_Accession_Number?: string
  Protein_Family_or_Domain?: string
  Reference_Genome_Version?: string
  Chromosome_Position?: string
  // ── 通用 - 终产物相关 ──
  Target_Metabolite_Product?: string
  Target_Metabolite_Class?: string
  Target_Product_Level_or_Property?: string
  Tissue_or_Organ_of_Metabolite_Assessment?: string
  Developmental_or_Physiological_Context?: string
  // ── 通用 - 代谢表型相关 ──
  Core_Phenotypic_Effect?: string
  Effect_Direction_on_Target_Product?: string
  Quantitative_Phenotypic_Alterations?: string
  Other_Phenotypic_Effects?: string
  // ── 通用 - 研究方法相关 ──
  Core_Validation_Method?: string
  Metabolite_Assay_Method?: string
  Gene_Discovery_or_Cloning_Method?: string
  Omics_Data?: string
  // ── 通用 - 群体相关 ──
  Genetic_Population?: string
  QTL_or_Locus_Name?: string
  Key_Variant_Type?: string
  Key_Variant_Site?: string
  Favorable_Allele?: string
  // ── 通用 - 应用相关 ──
  Key_Environment_or_Treatment_Factor?: string
  Field_Trials?: string
  Breeding_Application_Value?: string
  Potential_Tradeoffs?: string
  // ── 通用 - 其它 ──
  Notes_or_Other_Important_Info?: string
  // ── 合成特异 - 酶催化相关 ──
  Enzyme_Name?: string
  EC_Number?: string
  Catalyzed_Reaction_Description?: string
  Primary_Substrate?: string
  Primary_Product?: string
  Evidence_for_Enzymatic_Function?: string
  // ── 合成特异 - 途径位置相关 ──
  Biosynthetic_Pathway?: string
  Metabolic_Step_Position?: string
  Pathway_Branch_or_Subpathway?: string
  Evidence_for_Pathway_Position?: string
  // ── 合成特异 - 终产物影响相关 ──
  End_Product_Connection_Type?: string
  Directness_of_Effect_on_Target_Product?: string
  Rate_Limiting_or_Key_Control_Step?: string
  // ── 合成特异 - 互作相关 ──
  Cofactor_or_Coenzyme_Requirement?: string
  [key: string]: string | string[] | undefined
}

// 验证结果
export interface FieldVerdict {
  verdict: 'SUPPORTED' | 'UNSUPPORTED' | 'UNCERTAIN'
  reason: string
}

// 验证统计
export interface VerificationStats {
  supported: number
  unsupported: number
  uncertain: number
}

// 验证报告
export interface VerificationReport {
  file: string
  md_path: string
  json_path: string
  timestamp: string
  genes: {
    gene_index: number
    gene_name: string
    verification: Record<string, FieldVerdict>
    corrections: {
      field: string
      old_value: string
      new_value: string
      reason: string
    }[]
    stats: VerificationStats
  }[]
  summary: {
    total_fields: number
    supported: number
    unsupported: number
    uncertain: number
    total_corrections: number
  }
}

// 基因类别定义（v2 schema 支持 Pathway_Genes / Regulation_Genes / Common_Genes）
export const GENE_CATEGORIES = [
  { key: 'Pathway_Genes', label: 'Pathway Genes' },
  { key: 'Regulation_Genes', label: 'Regulation Genes' },
  { key: 'Common_Genes', label: 'Common Genes' },
] as const

// ── 字段顺序（与 nutri_fields_v2.xlsx 完全一致）──────────────
export const FIELD_ORDER: string[] = [
  // 通用 - 物种相关
  'Species_Common Name',
  'Species_Latin_Name',
  'Variety_or_Cultivar',
  // 通用 - 基因相关
  'Gene_Name',
  'Gene_Accession_Number',
  'Protein_Family_or_Domain',
  'Reference_Genome_Version',
  'Chromosome_Position',
  // 通用 - 终产物相关
  'Target_Metabolite_Product',
  'Target_Metabolite_Class',
  'Target_Product_Level_or_Property',
  'Tissue_or_Organ_of_Metabolite_Assessment',
  'Developmental_or_Physiological_Context',
  // 通用 - 代谢表型相关
  'Core_Phenotypic_Effect',
  'Effect_Direction_on_Target_Product',
  'Quantitative_Phenotypic_Alterations',
  'Other_Phenotypic_Effects',
  // 通用 - 研究方法相关
  'Core_Validation_Method',
  'Metabolite_Assay_Method',
  'Gene_Discovery_or_Cloning_Method',
  'Omics_Data',
  // 通用 - 群体相关
  'Genetic_Population',
  'QTL_or_Locus_Name',
  'Key_Variant_Type',
  'Key_Variant_Site',
  'Favorable_Allele',
  // 通用 - 应用相关
  'Key_Environment_or_Treatment_Factor',
  'Field_Trials',
  'Breeding_Application_Value',
  'Potential_Tradeoffs',
  // 通用 - 其它
  'Notes_or_Other_Important_Info',
  // 合成特异 - 酶催化相关
  'Enzyme_Name',
  'EC_Number',
  'Catalyzed_Reaction_Description',
  'Primary_Substrate',
  'Primary_Product',
  'Evidence_for_Enzymatic_Function',
  // 合成特异 - 途径位置相关
  'Biosynthetic_Pathway',
  'Metabolic_Step_Position',
  'Pathway_Branch_or_Subpathway',
  'Evidence_for_Pathway_Position',
  // 合成特异 - 终产物影响相关
  'End_Product_Connection_Type',
  'Directness_of_Effect_on_Target_Product',
  'Rate_Limiting_or_Key_Control_Step',
  // 合成特异 - 互作相关
  'Cofactor_or_Coenzyme_Requirement',
]

// 基因字段分组（用于 UI 展示）- 与 nutri_fields_v2.xlsx 分组一致
export const GENE_FIELD_GROUPS: { label: string; fields: string[] }[] = [
  {
    label: '物种相关',
    fields: [
      'Species_Common Name', 'Species_Latin_Name', 'Variety_or_Cultivar',
    ],
  },
  {
    label: '基因相关',
    fields: [
      'Gene_Name', 'Gene_Accession_Number', 'Protein_Family_or_Domain',
      'Reference_Genome_Version', 'Chromosome_Position',
    ],
  },
  {
    label: '终产物相关',
    fields: [
      'Target_Metabolite_Product', 'Target_Metabolite_Class',
      'Target_Product_Level_or_Property', 'Tissue_or_Organ_of_Metabolite_Assessment',
      'Developmental_or_Physiological_Context',
    ],
  },
  {
    label: '代谢表型相关',
    fields: [
      'Core_Phenotypic_Effect', 'Effect_Direction_on_Target_Product',
      'Quantitative_Phenotypic_Alterations', 'Other_Phenotypic_Effects',
    ],
  },
  {
    label: '研究方法相关',
    fields: [
      'Core_Validation_Method', 'Metabolite_Assay_Method',
      'Gene_Discovery_or_Cloning_Method', 'Omics_Data',
    ],
  },
  {
    label: '群体相关',
    fields: [
      'Genetic_Population', 'QTL_or_Locus_Name',
      'Key_Variant_Type', 'Key_Variant_Site', 'Favorable_Allele',
    ],
  },
  {
    label: '应用相关',
    fields: [
      'Key_Environment_or_Treatment_Factor', 'Field_Trials',
      'Breeding_Application_Value', 'Potential_Tradeoffs',
    ],
  },
  {
    label: '其它',
    fields: ['Notes_or_Other_Important_Info'],
  },
  {
    label: '酶催化相关（合成特异）',
    fields: [
      'Enzyme_Name', 'EC_Number', 'Catalyzed_Reaction_Description',
      'Primary_Substrate', 'Primary_Product', 'Evidence_for_Enzymatic_Function',
    ],
  },
  {
    label: '途径位置相关（合成特异）',
    fields: [
      'Biosynthetic_Pathway', 'Metabolic_Step_Position',
      'Pathway_Branch_or_Subpathway', 'Evidence_for_Pathway_Position',
    ],
  },
  {
    label: '终产物影响相关（合成特异）',
    fields: [
      'End_Product_Connection_Type', 'Directness_of_Effect_on_Target_Product',
      'Rate_Limiting_or_Key_Control_Step',
    ],
  },
  {
    label: '互作相关（合成特异）',
    fields: ['Cofactor_or_Coenzyme_Requirement'],
  },
]

// 字段中文名映射（与 nutri_fields_v2.xlsx 一致）
export const FIELD_LABELS: Record<string, string> = {
  // 通用 - 物种相关
  'Species_Common Name': '物种通用名',
  Species_Latin_Name: '物种拉丁名',
  Variety_or_Cultivar: '品种/栽培种',
  // 通用 - 基因相关
  Gene_Name: '基因名称',
  Gene_Accession_Number: '基因登录号',
  Protein_Family_or_Domain: '蛋白家族/结构域',
  Reference_Genome_Version: '参考基因组版本',
  Chromosome_Position: '染色体位置',
  // 通用 - 终产物相关
  Target_Metabolite_Product: '目标代谢产物',
  Target_Metabolite_Class: '目标代谢产物类别',
  Target_Product_Level_or_Property: '目标产物水平/性质',
  Tissue_or_Organ_of_Metabolite_Assessment: '代谢评估组织/器官',
  Developmental_or_Physiological_Context: '发育/生理背景',
  // 通用 - 代谢表型相关
  Core_Phenotypic_Effect: '核心表型效应',
  Effect_Direction_on_Target_Product: '对目标产物的效应方向',
  Quantitative_Phenotypic_Alterations: '定量表型变化',
  Other_Phenotypic_Effects: '其他表型效应',
  // 通用 - 研究方法相关
  Core_Validation_Method: '核心验证方法',
  Metabolite_Assay_Method: '代谢物分析方法',
  Gene_Discovery_or_Cloning_Method: '基因发现/克隆方法',
  Omics_Data: '组学数据',
  // 通用 - 群体相关
  Genetic_Population: '遗传群体',
  QTL_or_Locus_Name: 'QTL/位点名称',
  Key_Variant_Type: '变异类型',
  Key_Variant_Site: '变异位点',
  Favorable_Allele: '有利等位基因',
  // 通用 - 应用相关
  Key_Environment_or_Treatment_Factor: '环境/处理因素',
  Field_Trials: '田间试验',
  Breeding_Application_Value: '育种应用价值',
  Potential_Tradeoffs: '潜在权衡',
  // 通用 - 其它
  Notes_or_Other_Important_Info: '备注/其他重要信息',
  // 合成特异 - 酶催化相关
  Enzyme_Name: '酶名称',
  EC_Number: 'EC 编号',
  Catalyzed_Reaction_Description: '催化反应描述',
  Primary_Substrate: '主要底物',
  Primary_Product: '主要产物',
  Evidence_for_Enzymatic_Function: '酶功能证据',
  // 合成特异 - 途径位置相关
  Biosynthetic_Pathway: '生物合成途径',
  Metabolic_Step_Position: '代谢步骤位置',
  Pathway_Branch_or_Subpathway: '途径分支/子途径',
  Evidence_for_Pathway_Position: '途径位置证据',
  // 合成特异 - 终产物影响相关
  End_Product_Connection_Type: '终产物关联类型',
  Directness_of_Effect_on_Target_Product: '对目标产物效应的直接性',
  Rate_Limiting_or_Key_Control_Step: '限速/关键控制步骤',
  // 合成特异 - 互作相关
  Cofactor_or_Coenzyme_Requirement: '辅因子/辅酶需求',
}
