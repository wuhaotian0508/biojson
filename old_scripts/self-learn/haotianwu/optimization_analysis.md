# 🔬 代码结构优化分析 & 相关论文方法对比

---

## 一、相关论文/项目的实现方法

以下是学术界和工业界在 **"用 LLM 从科学文献中提取结构化信息"** 这个任务上的主要方法和系统：

### 1.1 多阶段提取 + 自我校验 (你当前的方法)

你的 pipeline 属于这一类：`提取 → 验证 → 修正`。

代表工作：
- **GENIA / BioCreative 系列** — 经典生物文本挖掘，但用的是传统 NLP（NER + RE），不是 LLM
- **LLM-based IE (GPT-4 / Claude)** — 2023-2025 年兴起的直接用大模型做信息提取

### 1.2 学术界主要方法对比

| 方法/论文 | 核心思路 | 与你的区别 |
|-----------|---------|-----------|
| **GeneTuring (Hou et al., 2023, Nature)** | 评估 LLM 在基因组学任务上的能力，包括基因功能标注 | 侧重 benchmark 评估，不是 pipeline |
| **BERN2 (Kim et al., 2023)** | 生物实体识别 + 规范化（传统 NER 模型） | 用专门训练的模型而非通用 LLM |
| **GeneGPT (Jin et al., 2024, Bioinformatics)** | LLM + NCBI API 工具调用，让 LLM 查数据库验证基因信息 | **关键差异**：用外部数据库回查，不只靠原文 |
| **BiomedRAG / PubMedGPT** | RAG（检索增强生成）+ 专用微调 | 引入检索增强，不只依赖单篇论文 |
| **Structured extraction with self-consistency (Wang et al., 2023)** | 多次采样 + 投票取共识 | 用多轮提取取交集减少幻觉 |
| **KGQA + NER pipelines (BioLink, etc.)** | 先 NER 识别实体 → 再 RE 抽取关系 → 组装 KG | 分步更细粒度 |
| **LlamaIndex / LangChain structured extraction** | 用 Pydantic 模型约束 LLM 输出格式 | 与你的 function_calling 类似，但用 Pydantic 做运行时验证 |

### 1.3 工业界常见模式

| 模式 | 描述 |
|------|------|
| **Map-Reduce 提取** | 长文档切片 → 每片独立提取 → 合并去重 |
| **Chain-of-Extraction** | 先粗提取（列出基因名）→ 再精提取（每个基因详细填写） |
| **Self-RAG** | 提取后自动检索原文段落验证每个 claim |
| **多 Agent 协作** | Extractor Agent + Verifier Agent + Merger Agent |

---

## 二、你的代码结构分析

### 2.1 当前架构

```
论文.md
  → md_to_json.py（单次 LLM 调用，一次提取所有基因的 42 个字段）
    → verify_response.py（逐基因调用 LLM 验证，每个基因一次调用）
      → 最终 verified JSON
```

### 2.2 做得好的地方 ✅

| 方面 | 评价 |
|------|------|
| **function_calling 约束输出格式** | 比自由文本 + 正则提取靠谱得多 |
| **自动验证 + 修正** | 两阶段架构比单次提取可靠 |
| **References 预处理** | 去除无用引用列表，节省 token |
| **Token 追踪** | 成本可控、可审计 |
| **Fallback 机制** | function_calling 不触发时有正则兜底 |
| **结构化 prompt 设计** | 角色 + 任务 + 步骤 + 约束，专业性强 |
| **目录分离** | raw → verified → reports，数据流清晰 |

---

## 三、可优化的地方 🔧

### 3.1 🔴 高优先级

#### ① 长文档分块提取（Map-Reduce）

**问题**：一篇论文可能有 60k+ tokens，一次性让 LLM 提取所有基因，容易遗漏后半部分的信息。

**优化**：
```
论文 → 按章节分块（Intro / Results / Methods / Figures）
     → 每块独立提取基因候选
     → 合并 + 去重 + 补全
```

**实现思路**：
```python
def split_by_sections(md_content):
    """按 # 标题分割章节"""
    sections = re.split(r'^(#{1,2}\s+.+)$', md_content, flags=re.MULTILINE)
    # 返回 [(标题, 内容), ...]
```

#### ② 两阶段提取（Chain-of-Extraction）

**问题**：42 个字段一次全部提取，LLM 的注意力分散，容易对不重要的字段编造值。

**优化**：
```
第 1 轮（粗提取）：只提取基因名 + 5 个核心字段
    → Gene_Name, Species, Final_Nutrient_Product, Core_Validation_Method, Gene_Role_Class
第 2 轮（精提取）：对每个已确认的基因，提取剩余 37 个字段
```

**好处**：
- 第 1 轮确保不遗漏基因
- 第 2 轮每个基因聚焦，提取质量更高
- 如果第 1 轮发现基因不是"核心基因"（只在 Discussion 提到），可以直接跳过

#### ③ 外部数据库回查验证

**问题**：当前验证只靠 LLM 重新读论文判断（self-verification），等于让"同一个考生检查自己的答案"。

**优化**：对关键字段用外部 API 验证：
```python
# 验证基因名是否存在
import requests
def verify_gene_name(gene_name, species):
    url = f"https://rest.ensembl.org/lookup/symbol/{species}/{gene_name}"
    resp = requests.get(url, headers={"Content-Type": "application/json"})
    return resp.status_code == 200

# 验证 EC 号
def verify_ec_number(ec_number):
    url = f"https://rest.uniprot.org/uniprotkb/search?query=ec:{ec_number}"
    # ...

# 验证 DOI
def verify_doi(doi):
    url = f"https://doi.org/{doi}"
    resp = requests.head(url, allow_redirects=True)
    return resp.status_code == 200
```

**可验证的字段**：Gene_Name, Gene_Accession_Number, EC_Number, DOI, Species_Latin_Name

---

### 3.2 🟡 中优先级

#### ④ Self-Consistency 投票

**问题**：单次提取可能因 temperature 导致结果不稳定。

**优化**：同一篇论文提取 3 次（temperature=0.3/0.5/0.7），对每个字段取"多数投票"：
```python
def self_consistency_extract(md_content, n_runs=3):
    results = [extract_once(md_content, temp=t) for t in [0.3, 0.5, 0.7]]
    # 对每个字段，取出现次数 ≥ 2 的值
    return majority_vote(results)
```

**代价**：token 消耗 ×3，适合重要论文或批量处理后的质量审计。

#### ⑤ 增量处理 & 跳过已处理文件

**问题**：每次 `run.sh all` 会重新处理所有 MD 文件，即使已经有提取结果。

**优化**：
```python
# md_to_json.py 中
output_path = os.path.join(OUTPUT_DIR, f'{filename}_nutri_plant.json')
if os.path.exists(output_path) and not os.getenv("FORCE_RERUN"):
    print(f"  ⏭️  已存在，跳过: {output_path}")
    return
```

#### ⑥ Pydantic 模型验证

**问题**：当前只靠 function_calling 约束格式，但 LLM 返回的值类型可能不对（比如该返回数组的字段返回了字符串）。

**优化**：用 Pydantic 做运行时验证：
```python
from pydantic import BaseModel, field_validator
from typing import Optional, List

class NutrientGene(BaseModel):
    Gene_Name: str
    Species: str
    Key_Intermediate_Metabolites_Affected: List[str] = ["NA"]
    EC_Number: str = "NA"
    
    @field_validator("EC_Number")
    def validate_ec(cls, v):
        if v != "NA" and not re.match(r'^\d+\.\d+\.\d+\.\d+$', v):
            return "NA"  # 格式不对就改成 NA
        return v
```

#### ⑦ 并行处理

**问题**：当前串行处理所有论文，7 篇论文 + 验证要很久。

**优化**：
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def process_all(files):
    with ThreadPoolExecutor(max_workers=3) as executor:
        loop = asyncio.get_event_loop()
        tasks = [loop.run_in_executor(executor, ai_response, f) for f in files]
        await asyncio.gather(*tasks)
```

---

### 3.3 🟢 低优先级（锦上添花）

#### ⑧ 提取论文中的图表信息

**现状**：MinerU 转的 Markdown 可能丢失图表中的关键数据（如 Figure 3 的通路图、Table S1 的数据）。

**优化**：对 PDF 中的图表用 VLM（视觉语言模型）单独提取，补充到 MD 中。

#### ⑨ 知识图谱构建

**现状**：每篇论文独立提取，基因之间的跨论文关系没有整合。

**优化**：提取后构建 Neo4j 知识图谱：
```
(Gene)-[CATALYZES]->(Reaction)-[PRODUCES]->(Metabolite)
(Gene)-[EXPRESSED_IN]->(Tissue)
(Gene)-[REGULATED_BY]->(TF)
```

#### ⑩ 错误重试 & 断点续传

**优化**：API 调用失败时自动重试，已处理的基因不重新验证：
```python
@retry(max_attempts=3, backoff=2)
def verify_gene_via_api(md_content, gene_data, gene_index):
    ...
```

---

## 四、优先级排序总结

| 优先级 | 优化项 | 预期收益 | 实现复杂度 |
|--------|--------|---------|-----------|
| 🔴 高 | ① 长文档分块提取 | 减少遗漏，提高完整性 | 中 |
| 🔴 高 | ② 两阶段提取 | 提高提取精度 | 中 |
| 🔴 高 | ③ 外部数据库回查 | 大幅降低幻觉率 | 中 |
| 🟡 中 | ④ Self-Consistency 投票 | 提高稳定性 | 低 |
| 🟡 中 | ⑤ 增量处理 | 避免重复消耗 | 低 |
| 🟡 中 | ⑥ Pydantic 验证 | 保证类型正确 | 低 |
| 🟡 中 | ⑦ 并行处理 | 加速 3-5× | 中 |
| 🟢 低 | ⑧ 图表信息提取 | 补全视觉信息 | 高 |
| 🟢 低 | ⑨ 知识图谱 | 跨论文整合 | 高 |
| 🟢 低 | ⑩ 错误重试 | 提高鲁棒性 | 低 |

---

## 五、建议的下一步

1. **先实现 ⑤ 增量处理**（最简单，5 分钟就搞定）
2. **再实现 ③ 外部数据库回查**（对 Gene_Name、EC_Number、DOI 做自动验证，显著提高可信度）
3. **然后考虑 ② 两阶段提取**（对论文提取质量影响最大）
