# Chunker 重构实施计划

> **目标**：把 RAG 的 chunk 生成逻辑从"单一扁平切法"升级为"按论文结构路由的分层切法"，同时支持增量索引与版本管理。
>
> **背景**：详见同目录下 `RAG_RETRIEVAL_ISSUES.md`。

---

## 目录

1. [目标 & 设计原则](#一目标--设计原则)
2. [总体架构](#二总体架构)
3. [模块划分](#三模块划分文件结构)
4. [核心数据类改造](#四核心数据类改造)
5. [类型路由规则](#五类型路由规则routerpy)
6. [公共字段分组常量](#六公共字段分组常量schemaspy)
7. [公共字段格式化器](#七公共字段格式化器field_formatterpy)
8. [BaseChunker](#八basechunkerbasepy)
9. [三个 chunker 的落地分工](#九三个-chunker-的落地分工)
10. [输出 content 的长度控制](#十输出-content-的统一长度控制)
11. [增量与版本控制](#十一增量与版本控制)
12. [实施阶段](#十二实施阶段推荐顺序)
13. [测试策略](#十三测试策略)
14. [关键配置开关](#十四关键配置开关供后续调参)
15. [风险与对策](#十五风险与对策)
16. [架构脑图](#十六一张脑图总结)
17. [第一个 commit 建议](#十七落地的第一个-commit-建议)

---

## 一、目标 & 设计原则

把前期讨论收敛到一个**可路由、可扩展、可增量**的 chunker 模块，覆盖三种主流论文结构，同时保持单一入口、统一输出。

**核心原则**：
1. **一个入口函数**：`chunk_paper(paper_json: dict) -> list[GeneChunk]`，外部调用方无需知道内部分型。
2. **路由而非分叉**：同一套字段清洗 / 格式化工具，由类型判断选不同的 chunk 组合策略。
3. **渐进式上线**：新老 chunker 可并存，用 `chunker_version` 标记，支持 A/B 对照。
4. **结构化 metadata**：chunk 的 metadata 里保留足够信息支持图式扩展、过滤检索、增量更新。

### 覆盖的三种论文结构

| 类型 | 典型文件 | 特征 | 处理 chunker |
|---|---|---|---|
| **新 schema Plant_Genes** | `35003178.json` | 单容器 `Plant_Genes`，有 `Contains_Gene_Molecular_Biology` 旗标 | `PlantGenesChunker` |
| **纯通路链型** | `10.1002@anie.202212301_*.json` | `Pathway_Genes` 多步酶反应链，共享终产物 | `PathwayChainChunker` |
| **三桶混合综述型** | `10.1007@s00122-019-03520-z_*.json` | `Common_Genes` + `Pathway_Genes` + `Regulation_Genes` 齐全 | `MixedBucketChunker` |
| **兜底** | 其它简单/稀有结构 | — | `GenericChunker` |

---

## 二、总体架构

```
┌─────────────────────────────────────────────────────────┐
│                    chunk_paper(paper)                    │
│                          ↓                               │
│                  PaperTypeRouter                         │
│          判断论文类型 → 选对应的 Chunker                 │
│          ┌────────┬─────────┬─────────┬────────┐         │
│          ↓        ↓         ↓         ↓        ↓         │
│   PlantGenes   Pathway   Mixed    Generic  (future)      │
│   Chunker      Chain     Bucket   Chunker                │
│                Chunker   Chunker                         │
│          └────────┴─────────┴─────────┴────────┘         │
│                          ↓                               │
│              共享的 FieldFormatter                       │
│       (NA 过滤、header 注入、字段清洗、翻译)              │
│                          ↓                               │
│                  List[GeneChunk]                         │
└─────────────────────────────────────────────────────────┘
```

---

## 三、模块划分（文件结构）

```
rag/utils/
├── data_loader.py              (保留，改造为只负责扫目录 + 调 chunker)
├── chunker/
│   ├── __init__.py             (导出 chunk_paper)
│   ├── router.py               (PaperTypeRouter + 类型判定)
│   ├── base.py                 (BaseChunker 抽象类 + 通用工具)
│   ├── field_formatter.py      (字段清洗、格式化、翻译、NA 过滤)
│   ├── plant_genes.py          (PlantGenesChunker)
│   ├── pathway_chain.py        (PathwayChainChunker)
│   ├── mixed_bucket.py         (MixedBucketChunker)
│   ├── generic.py              (GenericChunker — 兜底)
│   └── schemas.py              (字段分组常量、路由规则常量)
└── chunk_types.py              (GeneChunk 数据类扩展)
```

---

## 四、核心数据类改造

### `GeneChunk` 扩展（`chunk_types.py`）

现有字段保留，新增 metadata 维度：

```python
@dataclass
class GeneChunk:
    # ── 原有字段 ──
    gene_name: str
    paper_title: str
    journal: str
    doi: str
    gene_type: str          # Common_Genes / Pathway_Genes / Regulation_Genes
                            # / Plant_Genes / __PAPER__
    content: str

    # ── 新增字段 ──
    chunk_type: str         # paper_overview / pathway_graph / regulatory_network
                            # / common_gene / pathway_gene / regulation_gene
                            # / plant_gene_overview / plant_gene_mechanism / ...
    chunker_version: str    # "v2.2026-04" — 用于 A/B 与增量识别
    source_fields: list[str]# 本 chunk 覆盖了哪些原始 JSON 字段

    # ── 结构化关系（用于图式扩展）──
    metadata: dict          # 保留原始 gene JSON
    relations: dict         # {
                            #   "regulates":      [gene names],
                            #   "regulated_by":   [gene names],
                            #   "interacts_with": [gene names],
                            #   "substrate":      str,
                            #   "product":        str,
                            #   "pathway":        str,
                            # }
```

---

## 五、类型路由规则（`router.py`）

```python
def route(paper: dict) -> str:
    """根据 JSON 结构判定论文类型，返回 chunker key."""
    has_plant      = bool(paper.get("Plant_Genes"))
    has_common     = bool(paper.get("Common_Genes"))
    has_pathway    = bool(paper.get("Pathway_Genes"))
    has_regulation = bool(paper.get("Regulation_Genes"))

    # —— 新 schema ——
    if has_plant:
        return "plant_genes"

    # —— 三桶混合（至少同时出现 Pathway/Regulation，或三桶都有）——
    if (has_pathway and has_regulation) or (has_common and has_regulation):
        return "mixed_bucket"

    # —— 纯通路链（Pathway_Genes ≥ 3，且无调控桶）——
    if has_pathway and not has_regulation and len(paper["Pathway_Genes"]) >= 3:
        if _looks_like_linear_pathway(paper["Pathway_Genes"]):
            return "pathway_chain"
        return "generic"

    # —— 单桶或简单情况 ——
    return "generic"


def _looks_like_linear_pathway(genes: list[dict]) -> bool:
    """检查多个 gene 是否共享同一终产物 / 通路名。"""
    def _non_empty(v): return v not in (None, "NA", "", "null")
    terminals = {g.get("Terminal_Metabolite") for g in genes
                 if _non_empty(g.get("Terminal_Metabolite"))}
    pathways  = {g.get("Biosynthetic_Pathway")  for g in genes
                 if _non_empty(g.get("Biosynthetic_Pathway"))}
    return len(terminals) <= 2 and len(pathways) <= 2   # 容忍少量分支
```

---

## 六、公共字段分组常量（`schemas.py`）

集中维护三套字段分组，所有 chunker 共用。

### Plant_Genes (新 schema)

```python
PLANT_FIELD_GROUPS = {
    "identity": [
        "Gene_Name", "Gene_Accession_Number", "Chromosome_Position",
        "Species", "Species_Latin_Name", "Variety",
        "Reference_Genome_Version", "QTL_or_Locus_Name",
    ],
    "overview": [
        "Summary_key_Findings_of_Core_Gene",
        "Core_Phenotypic_Effect",
        "Research_Topic", "Trait_Category",
    ],
    "mechanism": [
        "Regulatory_Mechanism", "Regulatory_Pathway",
        "Biosynthetic_Pathway", "Upstream_or_Downstream_Regulation",
        "Protein_Family_or_Domain", "Subcellular_Localization",
        "Interacting_Proteins", "Expression_Pattern",
    ],
    "phenotype": [
        "Quantitative_Phenotypic_Alterations",
        "Other_Phenotypic_Effects",
        "Key_Environment_or_Treatment_Factor",
    ],
    "variant_breeding": [
        "Key_Variant_Site", "Key_Variant_Type",
        "Favorable_Allele", "Superior_Haplotype",
        "Breeding_Application_Value",
        "Field_Trials", "Genetic_Population",
        "Genomic_Selection_Application",
    ],
    "methods": [
        "Experimental_Methods", "Experimental_Materials",
        "Core_Validation_Method", "Gene_Discovery_or_Cloning_Method",
    ],
}
```

### Pathway_Genes

```python
PATHWAY_FIELD_GROUPS = {
    "identity":     ["Gene_Name", "Enzyme_Name", "EC_Number",
                     "Protein_Family_or_Domain", "Gene_Accession_Number"],
    "reaction":     ["Primary_Substrate", "Primary_Product",
                     "Catalyzed_Reaction_Description",
                     "Biosynthetic_Pathway",
                     "Pathway_Branch_or_Subpathway",
                     "Metabolic_Step_Position",
                     "End_Product_Connection_Type",
                     "Rate_Limiting_or_Key_Control_Step"],
    "terminal":     ["Terminal_Metabolite", "Terminal_Metabolite_Class",
                     "Terminal_Metabolite_Function",
                     "Terminal_Metabolite_Accumulation_Site"],
    "species_host": ["Source_Species", "Source_Species_Latin_Name",
                     "Applied_Species", "Applied_Species_Latin_Name",
                     "Source_Species_Variety", "Applied_Species_Variety"],
    "expression":   ["Expression_Pattern_of_Source_Species",
                     "Expression_Pattern_of_Applied_Species",
                     "Subcellular_Localization", "Applied_Promoters"],
    "function":     ["Core_Phenotypic_Effect",
                     "Summary_Key_Findings_of_Core_Gene",
                     "Core_Validation_Method",
                     "Environment_or_Treatment_Factor"],
    "interactions": ["Interacting_Proteins"],
    "engineering":  ["Breeding_or_Engineering_Application_Value",
                     "Potential_Tradeoffs",
                     "Other_Important_Info"],
}
```

### Regulation_Genes 独占字段（重点）

```python
REGULATION_CORE_FIELDS = [
    "Regulator_Type", "Regulation_Mode",
    "Primary_Regulatory_Targets", "Regulatory_Effect_on_Target_Genes",
    "Upstream_Signals_or_Inputs", "Metabolic_Process_Controlled",
    "Decisive_Influence_on_Target_Product",
    "Feedback_or_Feedforward_Regulation",
    "Protein_Complex_Involvement",
    "Epigenetic_Regulation",
]
```

### 空值判定 & 版本

```python
EMPTY_VALUES = (None, "NA", "", [], "null",
                "Not established", "not established")
CHUNKER_VERSION = "v2.2026-04"
```

---

## 七、公共字段格式化器（`field_formatter.py`）

```python
class FieldFormatter:
    def __init__(self, translation: dict[str, str]):
        self.translation = translation

    def render_group(self, gene: dict, fields: list[str],
                     section_title: str | None = None) -> list[str]:
        """渲染一个字段组，自动过滤 NA/null/空列表."""
        lines = []
        for field in fields:
            value = gene.get(field)
            if self._is_empty(value):
                continue
            key = self.translation.get(field, field)
            if isinstance(value, list):
                value = "; ".join(str(v) for v in value if not self._is_empty(v))
                if not value:
                    continue
            lines.append(f"{key}: {value}")
        if lines and section_title:
            lines = [f"── {section_title} ──"] + lines
        return lines

    @staticmethod
    def _is_empty(v) -> bool:
        if v is None:
            return True
        if isinstance(v, str) and v.strip() in (
                "NA", "", "null", "Not established", "not established"):
            return True
        if isinstance(v, list) and len(v) == 0:
            return True
        return False

    @staticmethod
    def header(paper: dict, gene: dict | None = None,
               extras: dict | None = None) -> list[str]:
        """统一的 header 行：Paper/Journal/DOI + 可选 Gene/Species."""
        lines = [
            f"[Paper] {paper.get('Title', '')}",
            f"[Journal] {paper.get('Journal', '')}  [DOI] {paper.get('DOI', '')}",
        ]
        if gene:
            if gene.get("Gene_Name"):
                gene_hdr = f"[Gene] {gene['Gene_Name']}"
                if gene.get("Enzyme_Name"):
                    gene_hdr += f"  [Enzyme] {gene['Enzyme_Name']}"
                if gene.get("Protein_Family_or_Domain"):
                    gene_hdr += f"  [Family] {gene['Protein_Family_or_Domain']}"
                lines.insert(0, gene_hdr)
            species = gene.get("Species_Latin_Name") \
                   or gene.get("Source_Species_Latin_Name")
            if species:
                lines.append(f"[Species] {species}")
        if extras:
            for k, v in extras.items():
                lines.append(f"[{k}] {v}")
        return lines
```

---

## 八、BaseChunker（`base.py`）

```python
class BaseChunker(ABC):
    chunker_key: str

    def __init__(self, formatter: FieldFormatter):
        self.fmt = formatter

    @abstractmethod
    def chunk(self, paper: dict) -> list[GeneChunk]: ...

    def _build_paper_overview(self, paper: dict,
                              gene_summary: str) -> GeneChunk:
        content_lines = self.fmt.header(paper)
        content_lines.append("")
        content_lines.append(gene_summary)
        return GeneChunk(
            gene_name="__PAPER__",
            paper_title=paper["Title"],
            journal=paper.get("Journal", ""),
            doi=paper.get("DOI", ""),
            gene_type="__PAPER__",
            chunk_type="paper_overview",
            chunker_version=CHUNKER_VERSION,
            content="\n".join(content_lines),
            source_fields=["Title", "Journal", "DOI"],
            metadata={},
            relations={},
        )

    @staticmethod
    def _parse_list_field(v) -> list[str]:
        """把 'O2; PBF1; OHP1' 这种分号串解析成 list."""
        if not v or v in EMPTY_VALUES:
            return []
        if isinstance(v, list):
            return [x.strip() for x in v if x]
        return [x.strip() for x in str(v).split(";") if x.strip()]
```

---

## 九、三个 chunker 的落地分工

### 9.1 `PlantGenesChunker`

对每个 `Plant_Genes[i]` 生成 **4–5 个 chunk**：

| chunk_type | 触发条件 | 字段组 |
|---|---|---|
| `plant_gene_overview` | 必出 | identity + overview |
| `plant_gene_mechanism` | mechanism 字段 ≥ 2 非空 | identity(header) + mechanism |
| `plant_gene_phenotype` | phenotype 字段 ≥ 1 非空 | identity(header) + phenotype |
| `plant_gene_variant_breeding` | variant_breeding ≥ 1 非空 | identity(header) + variant_breeding |
| `plant_gene_methods` | methods ≥ 1 非空 | identity(header) + methods |

Identity 字段**以 header 形式注入每个 chunk**，不单独成 chunk。

### 9.2 `PathwayChainChunker`

论文级 1 个 + gene 级 N 个 + 反应链 1 个：

| chunk_type | 数量 | 核心内容 |
|---|---|---|
| `pathway_overview` | 1 | 通路名 + 源物种 + 终产物 + gene 列表 + 反应概览 |
| `pathway_gene` | N | reaction 字段组靠前 + function + interactions + engineering |
| `pathway_graph` | 1 | 反应链拼接 + 分支酶 + 中间体目录 |

Gene 级 chunk **不重复** terminal/species 字段组（已吸收到 overview）。

`pathway_graph` 构建要点：
- 按 `Metabolic_Step_Position` 排序（Upstream → Midstream → Downstream）；
- 用 `Primary_Product[i] == Primary_Substrate[i+1]` 校验链序；
- 冗余酶（相同 substrate/product）并列；
- 分支酶（`End_Product_Connection_Type` 含 "Competes" / "Branch"）单列 Branch points 段。

### 9.3 `MixedBucketChunker`

论文级 1 个 + **网络 1 个** + 三桶 gene 各自：

| chunk_type | 数量 | 核心内容 |
|---|---|---|
| `paper_overview` | 1 | 三桶 gene 目录（按角色分组列） |
| `regulatory_network` | 1 | TF → targets + 上游 cascade + 蛋白互作图 + master regulator |
| `common_gene` | Nc | identity + role(terminal) + function + interactions + engineering |
| `pathway_gene` | Np | 同 `PathwayChainChunker` 的 pathway_gene 模板 |
| `regulation_gene` | Nr | **独占模板**：REGULATION_CORE_FIELDS 最前 + terminal + function + epigenetic |

`regulatory_network` 同时产出反向索引（不进向量）：

```python
network_index = {
    "regulates":    {"O2": ["19-kD α-zein", "22-kD α-zein", ...]},
    "regulated_by": {"27-kD γ-zein": ["O2", "PBF1", "OHP1", "OHP2"]},
    "interacts":    {"O2": ["PBF1", "OHP1", "OHP2", "ZmMADS47"]},
}
# 存到 index/relations.pkl
```

---

## 十、输出 content 的统一长度控制

每个 chunk 控制在 **200–800 字符**（不含 header）：

- `< 80` 字符：丢弃（信息量不足）；
- `> 1500` 字符：按字段组边界二次拆分（不按字符硬切）；
- 目标区间：**300–600** 字符，Jina v3 embedding 最稳区间。

```python
def _postprocess(self, chunks):
    result = []
    for c in chunks:
        body_len = len(c.content.split("\n", 3)[-1])
        if body_len < 80:
            continue
        if body_len > 1500:
            result.extend(self._split_oversized(c))
        else:
            result.append(c)
    return result
```

---

## 十一、增量与版本控制

### 索引文件结构升级

```
rag/index/
├── chunks.pkl          (全量 chunks)
├── embeddings.npy      (对应向量)
├── manifest.json       (每个 JSON 文件的 sha256 + chunker_version)
└── relations.pkl       (反向关系索引)
```

### 增量逻辑

```python
def build_index_incremental(self, data_dir, force=False):
    manifest = load_manifest()
    all_files = list(data_dir.glob("*_nutri_plant_verified.json"))

    to_rebuild, to_keep = [], []
    for f in all_files:
        sha = sha256_of(f)
        entry = manifest.get(f.name)
        if (not force
            and entry
            and entry["sha"] == sha
            and entry["chunker_version"] == CHUNKER_VERSION):
            to_keep.append(f.name)
        else:
            to_rebuild.append(f)

    # 清掉 to_rebuild 对应的老 chunks
    # 调 chunker 生成新 chunks
    # 只对新 chunks 调 embedding API
    # 合并 + 重写 chunks.pkl / embeddings.npy / manifest.json
```

**好处**：
- 新增 1 篇论文只花 1 篇的 embedding 钱；
- 修改 chunker 时 bump `CHUNKER_VERSION`，自动触发全量重建；
- 修改单篇 JSON 时只重建那篇。

---

## 十二、实施阶段（推荐顺序）

### Phase 1：骨架搭建（1–2 天）
- [ ] 建立 `chunker/` 目录结构 + `GeneChunk` 扩展字段
- [ ] 实现 `FieldFormatter`、`BaseChunker`、`schemas.py` 常量
- [ ] 实现 `router.py` + 单元测试（4–5 个代表性 JSON 测路由）

### Phase 2：逐个 chunker（各 1–2 天）
- [ ] `GenericChunker`（兜底，等价现有逻辑但接入新架构）
- [ ] `PlantGenesChunker`
- [ ] `PathwayChainChunker` + `pathway_graph` 构建算法
- [ ] `MixedBucketChunker` + `regulatory_network` + 反向索引

每个 chunker 用 3–5 篇代表性 JSON 做 snapshot test。

### Phase 3：改造 `data_loader.py`（0.5 天）
- [ ] `load_all_genes()` 改为调 `chunk_paper(paper)`
- [ ] 打印每个 chunker 的命中统计（路由分布）

### Phase 4：改造 `JinaRetriever`（0.5 天）
- [ ] `build_index()` → `build_index_incremental()`
- [ ] 新增 manifest 读写
- [ ] `search()` 接受 `chunk_type` / `gene_type` 过滤参数

### Phase 5：检索侧配合（1 天）
- [ ] `gene_db_search` 加参数 `prefer_chunk_types: list[str] | None`
- [ ] `rag_search` 聚合按 `(DOI, gene_name)` 去重 + 每 DOI 最多 3 个 chunk
- [ ] 可选：图式扩展（命中 Regulation_Gene → 自动带出其 targets）

### Phase 6：全量重建 + 评估（1 天）
- [ ] 全量 `build_index(force=True)`，估算 embedding 成本
- [ ] 测试集对比新老索引的 Recall@10
- [ ] 观察 chunk 数量分布、平均长度、每篇论文的 chunk 数

### Phase 7：上线与监控（0.5 天）
- [ ] 启动日志：chunker 版本、chunks 总数、chunk_type 分布、磁盘一致性检查
- [ ] CLI 工具：`python -m utils.chunker.debug <json_path>` 打印 chunk 预览

**总工期估算**：5–7 天，可并行（多个 chunker 相互独立）。

---

## 十三、测试策略

### 单元测试

对每个 chunker 准备"代表性 JSON" fixtures：
- `plant_genes_typical.json` — 所有字段组都有值
- `plant_genes_sparse.json`  — 一半 NA，检查跳过规则
- `pathway_chain.json`       — 3+ 步酶链
- `mixed_bucket.json`        — 三桶齐全
- `edge_single_gene.json`    — 单 gene，路由到 generic

### 路由测试

10 个真实 JSON 喂给 router，断言路由到预期 chunker。

### 快照测试

每个 chunker 对固定 fixture 产出固定 chunks（内容 hash 化），修改要对比 diff。

### 召回回归测试

准备 10 个 query（覆盖：基因名、通路名、TF 调控、中间体、表型、育种价值），记录 Recall@10 / MRR，新索引必须**不低于**老索引，且在 3 个以上 query 上有明显提升（+20% recall）。

---

## 十四、关键配置开关（供后续调参）

在 `core/config.py` 加：

```python
CHUNKER_VERSION = "v2.2026-04"
CHUNK_MIN_BODY_LEN = 80
CHUNK_MAX_BODY_LEN = 1500
CHUNK_TARGET_BODY_LEN = (300, 600)

# 各 chunk_type 在召回阶段的默认加权
CHUNK_TYPE_WEIGHTS = {
    "paper_overview":      1.0,
    "regulatory_network":  1.1,   # 轻微加权，少而密
    "pathway_graph":       1.1,
    "pathway_gene":        1.0,
    "regulation_gene":     1.0,
    "common_gene":         1.0,
    "plant_gene_overview": 1.0,
    "plant_gene_mechanism":0.95,
    "plant_gene_phenotype":0.95,
}

# 聚合规则
MAX_CHUNKS_PER_PAPER_IN_RESULTS = 3
```

---

## 十五、风险与对策

| 风险 | 对策 |
|---|---|
| 6700 篇全量重建 embedding 贵 | 先 100 篇 pilot 估成本；分批 + 预算审批 |
| 新旧索引并存期切换 | `USE_CHUNKER_V2` 环境变量灰度切换；秒级回滚 |
| `regulatory_network` 过大 | Regulation_Genes > 15 时按 target 聚类拆多个 |
| 路由误判（稀有结构） | Generic 兜底 + 日志记录所有 fallback 供人工审查 |
| `Primary_Regulatory_Targets` 里含自然语言而非分号列表 | 先 `;` 分隔，失败则整字段作文本保留；relations 表留空 |
| 跨语言检索不稳 | 后续加 BM25 hybrid，专有名词走关键词 |

---

## 十六、一张脑图总结

```
chunk_paper(paper)
  │
  ├── router.route(paper) ─┐
  │                        │
  │          ┌─────────────┼─────────────┐
  │          ↓             ↓             ↓
  │    plant_genes   pathway_chain   mixed_bucket   (+ generic)
  │          │             │             │
  │          │             │             ├── paper_overview      ──┐
  │          │             │             ├── regulatory_network  ──┤
  │          │             ├── pathway_overview                  ──┤
  │          │             ├── pathway_graph                     ──┤
  │          │             ├── N × pathway_gene                  ──┤
  │          ├── M × plant_gene_overview                         ──┤
  │          ├── M × plant_gene_mechanism                        ──┤
  │          ├── M × plant_gene_phenotype                        ──┤
  │          ├── M × plant_gene_variant_breeding                 ──┤
  │          ├── M × plant_gene_methods                          ──┤
  │                                      ├── Nc × common_gene    ──┤
  │                                      ├── Np × pathway_gene   ──┤
  │                                      ├── Nr × regulation_gene──┤
  │                                                               │
  │                                                               ↓
  │                                     FieldFormatter (统一渲染)
  │                                     ├── header()
  │                                     ├── render_group()
  │                                     ├── NA/null 过滤
  │                                     └── translate
  │                                                               │
  │                                                               ↓
  └── List[GeneChunk]
          ├── content           (嵌入文本)
          ├── chunk_type        (供过滤/加权)
          ├── source_fields     (可追溯)
          ├── metadata          (原始 gene JSON)
          └── relations         (图式扩展用)
```

---

## 十七、落地的第一个 commit 建议

如果今天开工，最小可合并的第一个 PR 建议**只包含**：

1. `chunker/base.py` + `field_formatter.py` + `schemas.py`
2. `chunker/generic.py`（行为等价于现有 `_create_gene_chunk`，但走新接口）
3. `chunker/router.py`（只实现分支，暂时全部 fallthrough 到 generic）
4. `data_loader.py` 改调 `chunk_paper()`
5. 回归测试：对 5 篇现有已索引论文跑 `load_all_genes()`，结果与老实现**字节一致**

这一步不改任何检索行为，只是引入新架构；然后后续每个 chunker 单独 PR、独立上线。

### 第一 PR 的验收标准

- [ ] `pytest` 通过所有新单元测试
- [ ] `python -m utils.chunker.debug <existing_indexed_json>` 输出与现有 chunks.pkl 对应条目字节一致
- [ ] `python -c "from utils.data_loader import DataLoader; DataLoader().load_all_genes()"` 产出的 chunk 数与现有索引一致（前 13 篇论文）
- [ ] 老的 `chunks.pkl` / `embeddings.npy` 不动，新架构跑 dry-run 对比

### 第一 PR 后的下一步（次日）

- [ ] 合并 `PlantGenesChunker` + 对应 fixtures 与测试
- [ ] 路由启用 `plant_genes` 分支
- [ ] 跑一次 pilot：只对 100 篇新 schema 的 JSON 构建新索引，手动对比 10 个 query 的召回

---

## 关联文档

- **问题诊断** → `RAG_RETRIEVAL_ISSUES.md`
- 现有向量检索模块 → `search/retriever.py`
- 现有 chunk 生成逻辑 → `utils/data_loader.py`
- 现有综合搜索工具 → `tools/rag_search.py`, `tools/gene_db_search.py`
- 现有配置 → `core/config.py`
