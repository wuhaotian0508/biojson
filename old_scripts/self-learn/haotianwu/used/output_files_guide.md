# 📂 输出文件导读指南

本文档说明各文件夹中文件的含义、结构和阅读方法。

---

## 一、目录结构与数据流

```
md/论文.md                                    ← 输入：MinerU 转换的论文 Markdown
    │
    ├──→ md_to_json.py（提取）
    │       ├──→ reports/raw_extractions/论文_nutri_plant.json    ← 初始提取结果
    │       └──→ reports/extract_tokens/token_usage_extract_*.json ← 提取 token 消耗
    │
    └──→ verify_response.py（验证）
            ├──→ json/论文_nutri_plant_verified.json               ← ✅ 最终结果
            ├──→ reports/verifications/论文_verification.json       ← 验证报告
            └──→ reports/verify_tokens/token_usage_verify_*.json   ← 验证 token 消耗
```

### 文件夹总览

| 文件夹 | 内容 | 由谁产生 |
|--------|------|---------|
| `json/` | **最终验证后的 JSON**（可直接使用） | `verify_response.py` |
| `reports/raw_extractions/` | 初始提取的 JSON（未验证） | `md_to_json.py` |
| `reports/verifications/` | 逐字段验证报告 | `verify_response.py` |
| `reports/extract_tokens/` | 提取阶段的 token 消耗 | `md_to_json.py` |
| `reports/verify_tokens/` | 验证阶段的 token 消耗 | `verify_response.py` |

---

## 二、`json/` 文件夹 — 最终结果（验证修正后）

存放 `*_nutri_plant_verified.json`，是经过验证后将 UNSUPPORTED（幻觉）字段修正为 `"NA"` 的版本。
**这是最终可信赖的版本，推荐直接使用。**

#### 结构示例：

```json
{
  "Title": "Rewiring of the Fruit Metabolome in Tomato Breeding",
  "Journal": "Cell",
  "DOI": "10.1016/j.cell.2017.12.019",
  "Genes": [
    {
      "Gene_Name": "Solyc10g085230",
      "Species": "Tomato",
      "Gene_Role_Class": "Enzyme",
      "Final_Nutrient_Product": "Steroidal glycoalkaloids (SGAs)",
      "Pathway_Name": "SGA biosynthesis",
      // ... 共 42-45 个字段
    }
  ]
}
```

#### 字段分类（42 个基因级字段）：

| 类别 | 字段 | 说明 |
|------|------|------|
| **基因身份** | Gene_Name, Gene_Accession_Number, Species, Species_Latin_Name, Variety, Reference_Genome_Version, Chromosome_Position | 基因是什么、在哪个物种 |
| **功能注释** | Gene_Role_Class, Protein_Family_or_Domain, Enzyme_Name_or_Function, EC_Number | 基因的功能角色 |
| **营养产物** | Final_Nutrient_Product, Final_Nutrient_Product_Class, Nutrient_Trait_Metric, Quantitative_Nutrient_Change, Units_and_Basis | 最终营养产物及其变化 |
| **代谢通路** | Pathway_Name, Metabolic_Step_Type, Reaction_Substrate, Reaction_Product_or_Immediate_Output, Key_Intermediate_Metabolites_Affected, Flux_or_Direction_Change | 代谢路径信息 |
| **表型效应** | Core_Phenotypic_Effect_on_Nutrient, Other_Phenotypic_Effects | 核心表型和副作用 |
| **调控网络** | Regulatory_Mechanism, Regulatory_Relationships, Interacting_Proteins | 调控机制和互作 |
| **时空表达** | Subcellular_Localization, Tissue_or_Organ_of_Nutrient_Accumulation, Developmental_Stage, Expression_Pattern | 在哪里、什么时候表达 |
| **环境因素** | Key_Environment_or_Treatment_Factor | 影响代谢的环境条件 |
| **实验验证** | Experimental_Materials, Core_Validation_Method, Nutrient_Assay_or_Profiling_Method, Omics_Data | 怎么验证的 |
| **遗传变异** | Key_Variant_Type, Key_Variant_Site, Favorable_Allele_or_Haplotype | 因果变异和有利等位基因 |
| **遗传分析** | Gene_Discovery_or_Cloning_Method, Genetic_Population, Field_Trials_or_GxE | 基因怎么发现的 |
| **育种价值** | Breeding_or_Biofortification_Value | 育种应用建议 |
| **总结** | Summary_key_Findings_of_Core_Gene, Notes_or_Other_Important_Info | 核心发现和备注 |

---

## 三、`reports/raw_extractions/` — 初始提取结果

存放 `*_nutri_plant.json`，是 LLM 直接提取的结果（**未经验证**）。

- 结构与 `json/` 中的 verified 文件完全一样
- 区别：可能包含 LLM 幻觉（编造的值）
- 用途：与 verified 版本对比，查看哪些字段被修正了

---

## 四、`reports/verifications/` — 验证报告 ⭐

存放 `*_verification.json`，记录了逐字段的验证判定。

#### 结构：

```json
{
  "file": "论文文件名",
  "md_path": "md/论文.md",
  "json_path": "reports/raw_extractions/论文_nutri_plant.json",
  "timestamp": "2026-03-13T20:55:22",
  "genes": [
    {
      "gene_index": 1,
      "gene_name": "Solyc10g085230",
      "verification": {
        "Gene_Name":  { "verdict": "SUPPORTED",   "reason": "论文中明确提到" },
        "EC_Number":  { "verdict": "UNSUPPORTED",  "reason": "论文未报告 EC 号" },
        "Variety":    { "verdict": "UNCERTAIN",    "reason": "描述不完全准确" }
      },
      "corrections": [
        { "field": "EC_Number", "old_value": "2.4.1.x", "new_value": "NA", "reason": "..." }
      ],
      "stats": { "supported": 16, "unsupported": 0, "uncertain": 23 }
    }
  ],
  "summary": {
    "total_fields": 111,
    "supported": 56,
    "unsupported": 0,
    "uncertain": 55,
    "total_corrections": 0
  }
}
```

#### 关键指标：

| 指标 | 含义 | 怎么看 |
|------|------|--------|
| `supported` | 有论文直接支持的字段数 | ✅ 越高越好 |
| `uncertain` | 不完全确定的字段数 | ❓ 需要人工复查 |
| `unsupported` | 找不到依据的字段数（幻觉） | ❌ 越低越好，会被自动改为 NA |
| `total_corrections` | 自动修正的字段数 | 🔧 = unsupported 的数量 |

#### 阅读技巧：
1. 先看 `summary` → `supported / total_fields × 100%` = 忠实度
2. 看 `corrections` 了解哪些字段被修正了
3. 对 `UNCERTAIN` 字段可以人工复查

---

## 五、`reports/extract_tokens/` 和 `reports/verify_tokens/` — Token 消耗

#### 命名规则：
```
token_usage_{extract|verify}_{日期}_{时间}.json
```

#### 结构：

```json
{
  "timestamp": "...",
  "model": "Vendor2/Claude-4.6-opus",
  "calls": [
    { "stage": "extract", "file": "论文.md", "prompt_tokens": 38030, "completion_tokens": 6451, "total_tokens": 44481 }
  ],
  "summary": {
    "extract": { "prompt_tokens": 38030, "completion_tokens": 6451, "total_tokens": 44481, "calls": 1 },
    "total":   { "prompt_tokens": 38030, "completion_tokens": 6451, "total_tokens": 44481, "calls": 1 }
  }
}
```

#### Token 指标：

| 字段 | 含义 |
|------|------|
| `prompt_tokens` | 输入 token（论文全文 + 指令 + Schema） |
| `completion_tokens` | 输出 token（提取/验证结果） |
| `total_tokens` | 总消耗 = prompt + completion，**计费依据** |

---

## 六、快速参考

| 目的 | 看哪个文件 |
|------|-----------|
| 使用提取结果 | `json/*_nutri_plant_verified.json` |
| 检查提取质量 | `reports/verifications/*_verification.json` → `summary` |
| 人工复查可疑字段 | `reports/verifications/` → 看 UNCERTAIN 字段 |
| 了解哪些字段被改了 | `reports/verifications/` → 看 `corrections` |
| 对比修正前后 | 对比 `reports/raw_extractions/` 和 `json/` |
| 监控 API 成本 | `reports/extract_tokens/` 或 `reports/verify_tokens/` → `summary.total` |
