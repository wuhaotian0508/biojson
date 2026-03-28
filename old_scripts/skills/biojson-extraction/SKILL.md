---
name: biojson-extraction
description: >
  BioJSON 论文基因提取与验证流水线。从论文 MD 中提取基因信息、分类、验证。
  核心特点：SKILL.md 定义所有 tools，代码硬编码 3 次 API 调用顺序。
version: 4.0.0
tags: [biojson, extraction, verification, llm, function-calling, skill-driven]

tools:
  # ── 提取阶段：4 个 tools ──
  - name: classify_genes
    handler: handlers.handle_classify
    description: >
      Identify ALL core genes from the paper's Results section and classify each into one of three categories:
      - Common: genes that are neither pathway enzymes nor regulators (e.g., general functional genes)
      - Pathway: genes encoding enzymes in biosynthetic/metabolic pathways (e.g., CHS, F3H, PSY, DAHPS)
      - Regulation: genes encoding transcription factors, signaling proteins, or other regulators (e.g., MYB12, Del, Ros1, SPL)
      Only include genes that are directly experimentally validated in the Results section.
    parameters:
      type: object
      properties:
        Title:
          type: string
          description: "Full paper title."
        Journal:
          type: string
          description: "Journal name."
        DOI:
          type: string
          description: "Pure DOI string, no URL prefix."
        genes:
          type: array
          description: "List of all core genes identified from the paper."
          items:
            type: object
            properties:
              Gene_Name:
                type: string
                description: "Gene name or symbol."
              category:
                type: string
                enum: ["Common", "Pathway", "Regulation"]
                description: "Gene category."
              reason:
                type: string
                description: "Brief reason for classification."
            required: ["Gene_Name", "category"]
      required: ["Title", "Journal", "DOI", "genes"]

  - name: extract_common_genes
    handler: handlers.handle_extract_common
    description: >
      Extract detailed field information for Common genes (genes that are neither pathway enzymes nor regulators).
      Only call this tool if classify_genes identified Common genes. If information is not found, use 'NA'.
    schema_ref: "configs/nutri_gene_schema_v2.json#CommonGeneExtraction"

  - name: extract_pathway_genes
    handler: handlers.handle_extract_pathway
    description: >
      Extract detailed field information for Pathway genes (genes encoding enzymes in biosynthetic/metabolic pathways).
      Only call this tool if classify_genes identified Pathway genes. If information is not found, use 'NA'.
    schema_ref: "configs/nutri_gene_schema_v2.json#PathwayGeneExtraction"

  - name: extract_regulation_genes
    handler: handlers.handle_extract_regulation
    description: >
      Extract detailed field information for Regulation genes (transcription factors, signaling proteins, regulators).
      Only call this tool if classify_genes identified Regulation genes. If information is not found, use 'NA'.
    schema_ref: "configs/nutri_gene_schema_v2.json#RegulationGeneExtraction"

  # ── 验证阶段：1 个 tool ──
  - name: verify_all_genes
    handler: handlers.handle_verify_all
    description: >
      Submit verification results for ALL genes at once.
      For each gene, provide verdicts for each non-NA field.
    parameters:
      type: object
      properties:
        gene_verdicts:
          type: array
          description: "Verification results grouped by gene."
          items:
            type: object
            properties:
              Gene_Name:
                type: string
                description: "The gene name being verified."
              field_verdicts:
                type: array
                description: "Verification results for each field of this gene."
                items:
                  type: object
                  properties:
                    field_name:
                      type: string
                      description: "The field name being verified."
                    verdict:
                      type: string
                      enum: ["SUPPORTED", "UNSUPPORTED", "UNCERTAIN"]
                      description: "Verification verdict."
                    reason:
                      type: string
                      description: "Brief explanation for the verdict."
                  required: ["field_name", "verdict", "reason"]
            required: ["Gene_Name", "field_verdicts"]
      required: ["gene_verdicts"]
---

# BioJSON 提取与验证流水线

## 架构概述：硬编码 3 次 API 调用

本技能采用 **代码硬编码** 控制 API 调用顺序，不依赖 LLM 自由选择 tool。

### 核心方法

| 方法 | 用途 |
|------|------|
| `registry.call_tool(tool_name)` | 强制调用指定的单个 tool（`tool_choice` 锁定） |
| `registry.call_tools([tool1, tool2])` | 提供多个 tool，让 LLM 并行调用 |

### 3 次 API 调用流程

```
SKILL.md (YAML: tool 定义)
    ↓ load_skill()
ToolRegistry (注册 tools + handlers)
    ↓ 代码硬编码控制

API Call #1: call_tool("classify_genes")
    ↓ handle_classify() → gene_dict 存入 state
    ↓ 代码读取 gene_dict，决定需要哪些 extract tools

API Call #2: call_tools(["extract_pathway_genes", "extract_regulation_genes"])
    ↓ handle_extract_*() → extraction 存入 state
    ↓ 代码保存 extraction.json + gene_dict.json

API Call #3: call_tool("verify_all_genes")
    ↓ handle_verify_all() → verify_results 存入 state
    ↓ 代码应用修正，保存 verified JSON
```

### 与旧架构（run_loop）的区别

| 维度 | 旧架构 (run_loop) | 新架构 (call_tool) |
|------|-------------------|-------------------|
| 控制权 | LLM 自由选择 tool | **代码硬编码**每步调哪个 tool |
| API 次数 | 不确定（1~5 轮） | **固定 3 次** |
| 可靠性 | LLM 可能跳过 extract | **不可能跳过**，代码强制调用 |
| 调试 | 难以预测 LLM 行为 | 每步都有明确的输入输出 |

## 项目结构

```
biojson/
├── configs/
│   ├── nutri_gene_prompt_v2.txt     # System Prompt
│   └── nutri_gene_schema_v2.json    # 三类基因的字段定义（schema_ref 引用）
├── scripts/
│   ├── tool_registry.py             # ★ ToolRegistry 类 + call_tool/call_tools
│   ├── pipeline.py                  # 流水线协调器
│   ├── md_to_json.py                # 提取：API #1 classify + API #2 extract
│   ├── verify_response.py           # 验证：API #3 verify
│   ├── text_utils.py                # MD 预处理
│   ├── token_tracker.py             # Token 用量追踪
│   └── run.sh                       # Shell 入口
├── skills/biojson-extraction/       # ★ 本技能
│   ├── SKILL.md                     # 本文件（tool 定义 + 操作手册）
│   ├── handlers.py                  # tool handler 实现
│   ├── check_extraction.py          # 批量检查提取质量
│   └── fix_string_genes.py          # 修复字符串数组问题
├── md/                              # 输入：论文 Markdown
├── reports/{paper-dir}/             # 中间产物
│   ├── extraction.json              # 提取结果
│   ├── gene_dict.json               # 基因分类字典
│   └── verification.json            # 验证报告
└── json/                            # 最终产物：verified JSON
```

## 数据流

### API Call #1: classify_genes（md_to_json.py）

**代码**: `registry.call_tool("classify_genes")` — 强制调用

| 输入 | 输出 |
|------|------|
| MD 论文全文 + system prompt | gene_dict: `{Gene_Name: category}` |

handler `handle_classify()` 解析 LLM 返回，存入 `state["gene_dict"]`。

### API Call #2: extract_*_genes（md_to_json.py）

**代码**: `registry.call_tools(needed_tools)` — 根据 gene_dict 决定调哪些

| 条件 | 调用的 tool |
|------|------------|
| gene_dict 有 Pathway 类 | `extract_pathway_genes` |
| gene_dict 有 Regulation 类 | `extract_regulation_genes` |
| gene_dict 有 Common 类 | `extract_common_genes` |

handler `handle_extract_*()` 解析 LLM 返回，存入 `state["extraction"]`。

### API Call #3: verify_all_genes（verify_response.py）

**代码**: `registry.call_tool("verify_all_genes")` — 强制调用

| 输入 | 输出 |
|------|------|
| MD 原文 + extraction JSON | 每个基因每个字段的 SUPPORTED/UNSUPPORTED/UNCERTAIN |

handler `handle_verify_all()` 解析验证结果，存入 `state["verify_results"]`。

## 运行方式

```bash
bash scripts/run.sh pipeline           # 全量
bash scripts/run.sh pipeline-test      # 测试第 1 个
bash scripts/run.sh pipeline-test 3    # 测试第 3 个
```

## Function Call 完整定义

以下是本技能所有 5 个 tool 的完整 OpenAI function calling JSON 格式。**这些定义与 `configs/nutri_gene_schema_v2.json` 严格一致**（实际运行时由 `tool_registry.py` 从 schema 动态构建）。

---

### Tool 1: `classify_genes`

```json
{
  "type": "function",
  "function": {
    "name": "classify_genes",
    "description": "Identify ALL core genes from the paper's Results section and classify each into one of three categories: Common / Pathway / Regulation.",
    "parameters": {
      "type": "object",
      "properties": {
        "Title":   { "type": "string", "description": "Full paper title." },
        "Journal": { "type": "string", "description": "Journal name." },
        "DOI":     { "type": "string", "description": "Pure DOI string, no URL prefix." },
        "genes": {
          "type": "array",
          "description": "List of all core genes identified from the paper.",
          "items": {
            "type": "object",
            "properties": {
              "Gene_Name": { "type": "string", "description": "Gene name or symbol." },
              "category":  { "type": "string", "enum": ["Common", "Pathway", "Regulation"], "description": "Gene category." },
              "reason":    { "type": "string", "description": "Brief reason for classification." }
            },
            "required": ["Gene_Name", "category"]
          }
        }
      },
      "required": ["Title", "Journal", "DOI", "genes"]
    }
  }
}
```

---

### Tool 2: `extract_common_genes`

Common 基因字段 = 24 个公共字段，不含酶特有字段和调控特有字段。

> 对应 Schema: `CommonGeneExtraction` → `$defs.CommonGene`

```json
{
  "type": "function",
  "function": {
    "name": "extract_common_genes",
    "description": "Extract detailed field information for Common genes.",
    "parameters": {
      "type": "object",
      "properties": {
        "genes": {
          "type": "array",
          "description": "Detailed information for each Common gene.",
          "items": {
            "type": "object",
            "properties": {
              "Gene_Name":                        { "type": "string", "description": "The name or symbol of the Core Gene, e.g., TaGS5, Pi2, BIK1." },
              "Gene_Accession_Number":             { "type": "string", "description": "Accession Number (e.g., NCBI, Ensembl, Phytozome ID, LOC_*, AT*, NCBI Locus Tag). Some IDs may be in figures or tables." },
              "Protein_Family_or_Domain":          { "type": "string", "description": "Protein family, enzyme class, TF family, domain architecture, or conserved motif relevant to the gene's function." },
              "Reference_Genome_Version":          { "type": "string", "description": "The reference genome version on which the coordinates are based, e.g., TAIR10, IRGSP-1.0, IWGSC1.0, GRCm39, GRCh38, ASM584v2." },
              "Species":                          { "type": "string", "description": "The main species studied (common name). e.g., Rice, Mouse, E. coli." },
              "Species_Latin_Name":               { "type": "string", "description": "The Latin name of the species, e.g., Oryza sativa, Mus musculus, Escherichia coli." },
              "Variety":                          { "type": "string", "description": "The specific variety or cultivar used in the study (e.g., Nipponbare, Zhonghua 11)." },
              "Gene_Origin_Species":              { "type": "string", "description": "Species in which the gene is naturally found or from which it was derived." },
              "Core_Phenotypic_Effect":            { "type": "string", "description": "The main conclusion about how the focal gene affects the target metabolite/product, e.g. promotes β-carotene accumulation; reduces phytic acid content; increases oleic acid proportion." },
              "Terminal_Metabolite":               { "type": "string", "description": "The primary terminal metabolite, e.g., β-carotene, anthocyanin, folate, tocopherol, lysine, oleic acid, resistant starch, iron, zinc, glucosinolate." },
              "Terminal_Metabolite_Class":          { "type": "string", "description": "Broad biochemical class of the terminal metabolite, e.g., carotenoid, flavonoid, vitamin, fatty acid, amino acid, alkaloid, terpenoid, polysaccharide, mineral nutrient." },
              "Terminal_Metabolite_Accumulation_Site": { "type": "string", "description": "Accumulation organs for terminal metabolite within a species (Note: This must be distinguished from the compound content of the species itself.)" },
              "Terminal_Metabolite_Function":       { "type": "string", "description": "The functions of the terminal metabolite, e.g., resistance to stress, drought, cold, pests, etc., or the treatment or alleviation of human diseases." },
              "Promoters":                        { "type": "string", "description": "Promoters and Their Types (Constitutive or Tissue-Specific)" },
              "Expression_Pattern":               { "type": "string", "description": "Tissues, developmental stages, or conditions with high gene expression, e.g., root, stress, or pathogen response." },
              "Subcellular_Localization":          { "type": "string", "description": "The location of the protein within the cell or subcellular fraction, e.g., Nucleus, Cell membrane, Chloroplast, Microsome." },
              "Interacting_Proteins":             { "type": "string", "description": "Experimentally validated interacting proteins or genes (list protein or gene name or ID, separated by semicolon ';')." },
              "Core_Validation_Method":            { "type": "string", "description": "Most critical functional validation approaches supporting the gene–metabolite mapping, e.g., knockout, overexpression, complementation, enzyme assay, transactivation assay, transient expression, metabolite profiling, isotope labeling." },
              "Omics_Data":                       { "type": "string", "description": "List the omics data types used in the study (e.g., RNA-seq, resequencing, metabolomics, single-cell) and their corresponding database accession numbers." },
              "Environment_or_Treatment_Factor":   { "type": "string", "description": "Environmental or treatment conditions directly affecting interpretation of the metabolic effect, e.g., light, temperature, nutrient supply, elicitor treatment, salt stress, pathogen infection, exogenous hormone, postharvest treatment." },
              "Breeding_Application_Value":        { "type": "string", "description": "Stated or inferred breeding relevance of the gene for nutritional improvement, biofortification, quality enhancement, or metabolic engineering." },
              "Potential_Tradeoffs":               { "type": "string", "description": "Growth penalty, yield change, stress susceptibility, off-target metabolic shifts." },
              "Summary_Key_Findings_of_Core_Gene": { "type": "string", "description": "Main findings in numbered format: '1. ... 2. ... 3. ...'. Focus on nutrient metabolism causality." },
              "Other_Important_Info":              { "type": "string", "description": "Important metabolism-related details not captured elsewhere, such as contradictory evidence, species-specific nuances, dual function, uncertain catalytic assignment, tissue-specific pathway divergence, or special caveats." }
            }
          }
        }
      },
      "required": ["genes"]
    }
  }
}
```

---

### Tool 3: `extract_pathway_genes`

Pathway 基因字段 = 公共字段（24 个）+ 酶/通路特有字段（10 个），共 34 个字段。

> 对应 Schema: `PathwayGeneExtraction` → `$defs.PathwayGene`

**酶特有字段（★ 标记）：** Enzyme_Name, EC_Number, Catalyzed_Reaction_Description, Primary_Substrate, Primary_Product, Biosynthetic_Pathway, Metabolic_Step_Position, Pathway_Branch_or_Subpathway, End_Product_Connection_Type, Rate_Limiting_or_Key_Control_Step

```json
{
  "type": "function",
  "function": {
    "name": "extract_pathway_genes",
    "description": "Extract detailed field information for Pathway genes (biosynthetic/metabolic enzyme genes).",
    "parameters": {
      "type": "object",
      "properties": {
        "genes": {
          "type": "array",
          "description": "Detailed information for each Pathway gene.",
          "items": {
            "type": "object",
            "properties": {
              "Gene_Name":                        { "type": "string", "description": "The name or symbol of the Core Gene, e.g., TaGS5, Pi2, BIK1." },
              "Gene_Accession_Number":             { "type": "string", "description": "Accession Number (e.g., NCBI, Ensembl, Phytozome ID, LOC_*, AT*, NCBI Locus Tag). Some IDs may be in figures or tables." },
              "Protein_Family_or_Domain":          { "type": "string", "description": "Protein family, enzyme class, TF family, domain architecture, or conserved motif relevant to the gene's function." },
              "Reference_Genome_Version":          { "type": "string", "description": "The reference genome version on which the coordinates are based, e.g., TAIR10, IRGSP-1.0, IWGSC1.0, GRCm39, GRCh38, ASM584v2." },
              "Species":                          { "type": "string", "description": "The main species studied (common name). e.g., Rice, Mouse, E. coli." },
              "Species_Latin_Name":               { "type": "string", "description": "The Latin name of the species, e.g., Oryza sativa, Mus musculus, Escherichia coli." },
              "Variety":                          { "type": "string", "description": "The specific variety or cultivar used in the study (e.g., Nipponbare, Zhonghua 11)." },
              "Gene_Origin_Species":              { "type": "string", "description": "Species in which the gene is naturally found or from which it was derived." },
              "Core_Phenotypic_Effect":            { "type": "string", "description": "The main conclusion about how the focal gene affects the target metabolite/product." },
              "Terminal_Metabolite":               { "type": "string", "description": "The primary terminal metabolite, e.g., β-carotene, anthocyanin, folate, tocopherol, lysine, oleic acid, resistant starch, iron, zinc, glucosinolate." },
              "Terminal_Metabolite_Class":          { "type": "string", "description": "Broad biochemical class of the terminal metabolite, e.g., carotenoid, flavonoid, vitamin, fatty acid, amino acid, alkaloid, terpenoid, polysaccharide, mineral nutrient." },
              "Terminal_Metabolite_Accumulation_Site": { "type": "string", "description": "Accumulation organs for terminal metabolite within a species." },
              "Terminal_Metabolite_Function":       { "type": "string", "description": "The functions of the terminal metabolite, e.g., resistance to stress, drought, cold, pests, etc., or the treatment or alleviation of human diseases." },
              "Promoters":                        { "type": "string", "description": "Promoters and Their Types (Constitutive or Tissue-Specific)" },
              "Expression_Pattern":               { "type": "string", "description": "Tissues, developmental stages, or conditions with high gene expression." },
              "Subcellular_Localization":          { "type": "string", "description": "The location of the protein within the cell or subcellular fraction." },
              "Interacting_Proteins":             { "type": "string", "description": "Experimentally validated interacting proteins or genes (separated by semicolon ';')." },
              "Core_Validation_Method":            { "type": "string", "description": "Most critical functional validation approaches supporting the gene–metabolite mapping." },
              "Omics_Data":                       { "type": "string", "description": "List the omics data types used in the study and their corresponding database accession numbers." },
              "Environment_or_Treatment_Factor":   { "type": "string", "description": "Environmental or treatment conditions directly affecting interpretation of the metabolic effect." },
              "Breeding_Application_Value":        { "type": "string", "description": "Stated or inferred breeding relevance of the gene for nutritional improvement, biofortification, quality enhancement, or metabolic engineering." },
              "Potential_Tradeoffs":               { "type": "string", "description": "Growth penalty, yield change, stress susceptibility, off-target metabolic shifts." },
              "Summary_Key_Findings_of_Core_Gene": { "type": "string", "description": "Main findings in numbered format: '1. ... 2. ... 3. ...'. Focus on nutrient metabolism causality." },
              "Other_Important_Info":              { "type": "string", "description": "Important metabolism-related details not captured elsewhere." },

              "Enzyme_Name":                      { "type": "string", "description": "★ Standard enzyme name corresponding to the focal gene product." },
              "EC_Number":                        { "type": "string", "description": "★ Enzyme Commission number if reported or confidently inferable from the paper's enzyme assignment." },
              "Catalyzed_Reaction_Description":    { "type": "string", "description": "★ The biochemical reaction catalyzed by the enzyme, e.g., converts phytoene to ζ-carotene through desaturation; hydroxylates β-carotene to zeaxanthin." },
              "Primary_Substrate":                { "type": "string", "description": "★ Main substrate(s) used by the enzyme in the relevant metabolic step." },
              "Primary_Product":                  { "type": "string", "description": "★ Immediate product(s) generated by the enzyme in the relevant step." },
              "Biosynthetic_Pathway":             { "type": "string", "description": "★ Name of the metabolic or biosynthetic pathway to which the focal gene is assigned." },
              "Metabolic_Step_Position":           { "type": "string", "description": "★ Relative position of the enzymatic step within the pathway: upstream, midstream, downstream, terminal step, branch point, committed step, side-route, salvage/recycling step." },
              "Pathway_Branch_or_Subpathway":      { "type": "string", "description": "★ Specific branch, module, or subpathway in which the enzyme functions, e.g., β-branch of carotenoid pathway; flavonol branch; tocopherol cyclization branch." },
              "End_Product_Connection_Type":        { "type": "string", "description": "★ How the catalytic step connects to the target product: directly forms target product, forms immediate precursor, supplies precursor pool, diverts flux toward target product, competes with target-product branch, required for storage/modification of target product." },
              "Rate_Limiting_or_Key_Control_Step":  { "type": "string", "description": "★ Whether the paper supports this enzyme as a rate-limiting enzyme, key control point, committed-step enzyme, terminal determinant, branch-switch enzyme, bottleneck enzyme, or not established." }
            }
          }
        }
      },
      "required": ["genes"]
    }
  }
}
```

---

### Tool 4: `extract_regulation_genes`

Regulation 基因字段 = 公共字段（24 个）+ 调控特有字段（9 个），共 33 个字段。

> 对应 Schema: `RegulationGeneExtraction` → `$defs.RegulationGene`

**调控特有字段（★ 标记）：** Regulator_Type, Direct_or_Indirect_Regulator, Regulation_Mode, Upstream_Signals_or_Inputs, Primary_Regulatory_Targets, Regulatory_Effect_on_Target_Genes, Decisive_Influence_on_Target_Product, Metabolic_Process_Controlled, Feedback_or_Feedforward_Regulation

```json
{
  "type": "function",
  "function": {
    "name": "extract_regulation_genes",
    "description": "Extract detailed field information for Regulation genes (transcription factors, signaling proteins, regulators).",
    "parameters": {
      "type": "object",
      "properties": {
        "genes": {
          "type": "array",
          "description": "Detailed information for each Regulation gene.",
          "items": {
            "type": "object",
            "properties": {
              "Gene_Name":                        { "type": "string", "description": "The name or symbol of the Core Gene, e.g., TaGS5, Pi2, BIK1." },
              "Gene_Accession_Number":             { "type": "string", "description": "Accession Number (e.g., NCBI, Ensembl, Phytozome ID, LOC_*, AT*, NCBI Locus Tag). Some IDs may be in figures or tables." },
              "Protein_Family_or_Domain":          { "type": "string", "description": "Protein family, enzyme class, TF family, domain architecture, or conserved motif relevant to the gene's function." },
              "Reference_Genome_Version":          { "type": "string", "description": "The reference genome version on which the coordinates are based, e.g., TAIR10, IRGSP-1.0, IWGSC1.0, GRCm39, GRCh38, ASM584v2." },
              "Species":                          { "type": "string", "description": "The main species studied (common name). e.g., Rice, Mouse, E. coli." },
              "Species_Latin_Name":               { "type": "string", "description": "The Latin name of the species, e.g., Oryza sativa, Mus musculus, Escherichia coli." },
              "Variety":                          { "type": "string", "description": "The specific variety or cultivar used in the study (e.g., Nipponbare, Zhonghua 11)." },
              "Gene_Origin_Species":              { "type": "string", "description": "Species in which the gene is naturally found or from which it was derived." },
              "Core_Phenotypic_Effect":            { "type": "string", "description": "The main conclusion about how the focal gene affects the target metabolite/product." },
              "Terminal_Metabolite":               { "type": "string", "description": "The primary terminal metabolite, e.g., β-carotene, anthocyanin, folate, tocopherol, lysine, oleic acid, resistant starch, iron, zinc, glucosinolate." },
              "Terminal_Metabolite_Class":          { "type": "string", "description": "Broad biochemical class of the terminal metabolite, e.g., carotenoid, flavonoid, vitamin, fatty acid, amino acid, alkaloid, terpenoid, polysaccharide, mineral nutrient." },
              "Terminal_Metabolite_Accumulation_Site": { "type": "string", "description": "Accumulation organs for terminal metabolite within a species." },
              "Terminal_Metabolite_Function":       { "type": "string", "description": "The functions of the terminal metabolite, e.g., resistance to stress, drought, cold, pests, etc., or the treatment or alleviation of human diseases." },
              "Promoters":                        { "type": "string", "description": "Promoters and Their Types (Constitutive or Tissue-Specific)" },
              "Expression_Pattern":               { "type": "string", "description": "Tissues, developmental stages, or conditions with high gene expression." },
              "Subcellular_Localization":          { "type": "string", "description": "The location of the protein within the cell or subcellular fraction." },
              "Interacting_Proteins":             { "type": "string", "description": "Experimentally validated interacting proteins or genes (separated by semicolon ';')." },
              "Core_Validation_Method":            { "type": "string", "description": "Most critical functional validation approaches supporting the gene–metabolite mapping." },
              "Omics_Data":                       { "type": "string", "description": "List the omics data types used in the study and their corresponding database accession numbers." },
              "Environment_or_Treatment_Factor":   { "type": "string", "description": "Environmental or treatment conditions directly affecting interpretation of the metabolic effect." },
              "Breeding_Application_Value":        { "type": "string", "description": "Stated or inferred breeding relevance of the gene for nutritional improvement, biofortification, quality enhancement, or metabolic engineering." },
              "Potential_Tradeoffs":               { "type": "string", "description": "Growth penalty, yield change, stress susceptibility, off-target metabolic shifts." },
              "Summary_Key_Findings_of_Core_Gene": { "type": "string", "description": "Main findings in numbered format: '1. ... 2. ... 3. ...'. Focus on nutrient metabolism causality." },
              "Other_Important_Info":              { "type": "string", "description": "Important metabolism-related details not captured elsewhere." },

              "Regulator_Type":                    { "type": "string", "description": "★ Type of regulator, e.g., transcription factor, signaling kinase, phosphatase, E3 ligase, transporter regulator, RNA-binding protein, chromatin modifier, miRNA-related factor, scaffold protein, hormone-response regulator, etc." },
              "Direct_or_Indirect_Regulator":      { "type": "string", "description": "★ Whether the gene regulates the target metabolic process directly, indirectly, or with unresolved directness." },
              "Regulation_Mode":                   { "type": "string", "description": "★ Mode of regulation, e.g., transcriptional activation, transcriptional repression, chromatin opening, protein stabilization, ubiquitin-mediated degradation, phosphorylation activation, dephosphorylation, RNA silencing, translation control, transport control, feedback regulation." },
              "Upstream_Signals_or_Inputs":         { "type": "string", "description": "★ Signals, hormones, nutrients, stresses, or developmental cues acting upstream of the regulator." },
              "Primary_Regulatory_Targets":         { "type": "string", "description": "★ The principal downstream genes, enzymes, transporters, or pathway modules regulated by the focal gene." },
              "Regulatory_Effect_on_Target_Genes":  { "type": "string", "description": "★ Directional effect on key downstream metabolic genes, e.g., activates PSY1 and LCYB; represses FAD2; stabilizes PAP1; promotes degradation of enzyme E." },
              "Decisive_Influence_on_Target_Product": { "type": "string", "description": "★ Clear statement of why this regulator is considered decisive for the target product, e.g., master regulator, major switch, essential activator, strong repressor, condition-dependent controller, ripening-specific inducer, nutrient-responsive regulator." },
              "Metabolic_Process_Controlled":       { "type": "string", "description": "★ The controlled metabolic process, e.g., biosynthesis, degradation, transport, sequestration, precursor supply, branch selection, remodeling, storage deposition, or feedback homeostasis." },
              "Feedback_or_Feedforward_Regulation": { "type": "string", "description": "★ Whether the regulator participates in feedback, feedforward, autoregulation, metabolite-dependent repression/activation, or homeostatic loops." }
            }
          }
        }
      },
      "required": ["genes"]
    }
  }
}
```

---

### Tool 5: `verify_all_genes`

```json
{
  "type": "function",
  "function": {
    "name": "verify_all_genes",
    "description": "Submit verification results for ALL genes at once. For each gene, provide verdicts for each non-NA field.",
    "parameters": {
      "type": "object",
      "properties": {
        "gene_verdicts": {
          "type": "array",
          "description": "Verification results grouped by gene.",
          "items": {
            "type": "object",
            "properties": {
              "Gene_Name": { "type": "string", "description": "The gene name being verified." },
              "field_verdicts": {
                "type": "array",
                "description": "Verification results for each field of this gene.",
                "items": {
                  "type": "object",
                  "properties": {
                    "field_name": { "type": "string", "description": "The field name being verified." },
                    "verdict":    { "type": "string", "enum": ["SUPPORTED", "UNSUPPORTED", "UNCERTAIN"], "description": "Verification verdict." },
                    "reason":     { "type": "string", "description": "Brief explanation for the verdict." }
                  },
                  "required": ["field_name", "verdict", "reason"]
                }
              }
            },
            "required": ["Gene_Name", "field_verdicts"]
          }
        }
      },
      "required": ["gene_verdicts"]
    }
  }
}
```

---

## 常见故障排查

### 1. classify 返回空基因列表
代码会打印 `⚠️ classify 返回空基因列表`，跳过 API #2。检查 MD 文件是否有 Results 部分。

### 2. JSON 截断
`ToolRegistry._repair_truncated_json()` 自动修复。

### 3. 字符串数组（基因是字符串而非对象）
`handlers.py` 中的 `_handle_extract()` 自动检测并修复。

### 4. 添加新 tool
1. 在本文件 YAML 的 `tools:` 下添加 tool 定义
2. 在 `handlers.py` 中添加对应的 handler 函数
3. 在 `md_to_json.py` 或 `verify_response.py` 中用 `call_tool()` 硬编码调用
