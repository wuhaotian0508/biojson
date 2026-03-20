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
  expert_verdict: 'correct' | 'incorrect' | 'modified'
  corrected_value: string | null
  comment: string | null
  annotator_id: string | null
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

// 单个基因的字段（40+ 个字段）
export interface GeneData {
  Gene_Name?: string
  Gene_Accession_Number?: string
  Species?: string
  Species_Latin_Name?: string
  Variety?: string
  Reference_Genome_Version?: string
  Chromosome_Position?: string
  Gene_Role_Class?: string
  Protein_Family_or_Domain?: string
  Enzyme_Name_or_Function?: string
  EC_Number?: string
  Final_Nutrient_Product?: string
  Final_Nutrient_Product_Class?: string
  Nutrient_Trait_Metric?: string
  Quantitative_Nutrient_Change?: string
  Units_and_Basis?: string
  Pathway_Name?: string
  Metabolic_Step_Type?: string
  Reaction_Substrate?: string
  Reaction_Product_or_Immediate_Output?: string
  Key_Intermediate_Metabolites_Affected?: string[] | string
  Flux_or_Direction_Change?: string
  Core_Phenotypic_Effect_on_Nutrient?: string
  Other_Phenotypic_Effects?: string
  Regulatory_Mechanism?: string
  Regulatory_Relationships?: string
  Interacting_Proteins?: string[] | string
  Subcellular_Localization?: string
  Tissue_or_Organ_of_Nutrient_Accumulation?: string
  Developmental_Stage?: string
  Expression_Pattern?: string
  Key_Environment_or_Treatment_Factor?: string
  Experimental_Materials?: string
  Core_Validation_Method?: string
  Nutrient_Assay_or_Profiling_Method?: string
  Omics_Data?: string
  Key_Variant_Type?: string
  Key_Variant_Site?: string
  Favorable_Allele_or_Haplotype?: string
  Gene_Discovery_or_Cloning_Method?: string
  Genetic_Population?: string
  Field_Trials_or_GxE?: string
  Breeding_or_Biofortification_Value?: string
  Summary_key_Findings_of_Core_Gene?: string
  Notes_or_Other_Important_Info?: string
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

// 基因字段分组（用于 UI 展示）- 通用字段
export const GENE_FIELD_GROUPS: { label: string; fields: string[] }[] = [
  {
    label: '基本信息',
    fields: [
      'Gene_Name', 'Gene_Accession_Number', 'Species', 'Species_Latin_Name',
      'Variety', 'Reference_Genome_Version', 'Chromosome_Position',
    ],
  },
  {
    label: '功能角色',
    fields: [
      'Gene_Role_Class', 'Protein_Family_or_Domain', 'Enzyme_Name_or_Function', 'EC_Number',
    ],
  },
  {
    label: '营养产物',
    fields: [
      'Final_Nutrient_Product', 'Final_Nutrient_Product_Class', 'Nutrient_Trait_Metric',
      'Quantitative_Nutrient_Change', 'Units_and_Basis',
    ],
  },
  {
    label: '代谢通路',
    fields: [
      'Pathway_Name', 'Metabolic_Step_Type', 'Reaction_Substrate',
      'Reaction_Product_or_Immediate_Output', 'Key_Intermediate_Metabolites_Affected',
      'Flux_or_Direction_Change',
    ],
  },
  {
    label: '表型效应',
    fields: ['Core_Phenotypic_Effect_on_Nutrient', 'Other_Phenotypic_Effects'],
  },
  {
    label: '调控机制',
    fields: ['Regulatory_Mechanism', 'Regulatory_Relationships', 'Interacting_Proteins'],
  },
  {
    label: '定位与表达',
    fields: [
      'Subcellular_Localization', 'Tissue_or_Organ_of_Nutrient_Accumulation',
      'Developmental_Stage', 'Expression_Pattern', 'Key_Environment_or_Treatment_Factor',
    ],
  },
  {
    label: '实验验证',
    fields: [
      'Experimental_Materials', 'Core_Validation_Method',
      'Nutrient_Assay_or_Profiling_Method', 'Omics_Data',
    ],
  },
  {
    label: '变异信息',
    fields: [
      'Key_Variant_Type', 'Key_Variant_Site', 'Favorable_Allele_or_Haplotype',
    ],
  },
  {
    label: '遗传与育种',
    fields: [
      'Gene_Discovery_or_Cloning_Method', 'Genetic_Population',
      'Field_Trials_or_GxE', 'Breeding_or_Biofortification_Value',
    ],
  },
  {
    label: '总结',
    fields: ['Summary_key_Findings_of_Core_Gene', 'Notes_or_Other_Important_Info'],
  },
]

// 字段中文名映射
export const FIELD_LABELS: Record<string, string> = {
  Gene_Name: '基因名称',
  Gene_Accession_Number: '基因登录号',
  Species: '物种',
  Species_Latin_Name: '物种拉丁名',
  Variety: '品种',
  Reference_Genome_Version: '参考基因组版本',
  Chromosome_Position: '染色体位置',
  Gene_Role_Class: '基因角色',
  Protein_Family_or_Domain: '蛋白家族/结构域',
  Enzyme_Name_or_Function: '酶名/功能',
  EC_Number: 'EC 编号',
  Final_Nutrient_Product: '最终营养产物',
  Final_Nutrient_Product_Class: '营养产物类别',
  Nutrient_Trait_Metric: '营养性状度量',
  Quantitative_Nutrient_Change: '定量变化',
  Units_and_Basis: '单位/基准',
  Pathway_Name: '通路名称',
  Metabolic_Step_Type: '代谢步骤类型',
  Reaction_Substrate: '反应底物',
  Reaction_Product_or_Immediate_Output: '反应产物',
  Key_Intermediate_Metabolites_Affected: '关键中间代谢物',
  Flux_or_Direction_Change: '通量/方向变化',
  Core_Phenotypic_Effect_on_Nutrient: '核心表型效应',
  Other_Phenotypic_Effects: '其他表型效应',
  Regulatory_Mechanism: '调控机制',
  Regulatory_Relationships: '调控关系',
  Interacting_Proteins: '互作蛋白',
  Subcellular_Localization: '亚细胞定位',
  Tissue_or_Organ_of_Nutrient_Accumulation: '营养积累组织',
  Developmental_Stage: '发育阶段',
  Expression_Pattern: '表达模式',
  Key_Environment_or_Treatment_Factor: '环境/处理因素',
  Experimental_Materials: '实验材料',
  Core_Validation_Method: '核心验证方法',
  Nutrient_Assay_or_Profiling_Method: '营养分析方法',
  Omics_Data: '组学数据',
  Key_Variant_Type: '变异类型',
  Key_Variant_Site: '变异位点',
  Favorable_Allele_or_Haplotype: '有利等位基因/单倍型',
  Gene_Discovery_or_Cloning_Method: '基因发现/克隆方法',
  Genetic_Population: '遗传群体',
  Field_Trials_or_GxE: '田间试验/GxE',
  Breeding_or_Biofortification_Value: '育种/生物强化价值',
  Summary_key_Findings_of_Core_Gene: '核心发现总结',
  Notes_or_Other_Important_Info: '备注',
}
