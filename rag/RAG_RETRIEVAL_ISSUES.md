# RAG 检索失败问题诊断与修复建议

> **问题起点**：用户测试查询 "番茄和马铃薯主要积累 25S 构型的生物碱（如 α-番茄碱），而茄子则主要积累 25R 构型的生物碱（如 α-澳洲茄胺），这两种生物碱的生物学功能分别是什么？由什么基因决定其不同构型形式" 检索不到正确答案（答案位于 `data/10.1038@s41467-025-59290-4_nutri_plant_verified.json`），但加上论文标题 `"Enzymatic twists evolved stereo-divergent alkaloids in the Solanaceae family"` + 期刊 `"Nature Plants"` 就能找到。
>
> **结论**：不是单一 bug，而是多层问题叠加的结果，按严重程度从底层到上层依次列出。

---

## 一、现象观察

- 查询不加论文标题 → 答案相关字段排不到向量相似度 top 10；
- 返回 10 篇"毫不相干"的参考文献；
- 加上 `Title` + `Journal` 的提示后，检索能命中对应论文。

---

## 二、根本原因（按严重程度）

### 🔴 问题 1：向量索引严重过时（最根本）

| 项 | 数值 |
|---|---|
| `rag/data/` 下 `*_verified.json` 文件数 | **6753** |
| `index/chunks.pkl` 实际索引的 gene chunk 数 | **70** |
| `index/embeddings.npy` 形状 | **(70, 1024)** |
| 索引构建时间 | **2026-03-29 15:16** |
| 目标论文 JSON 修改时间 | **2026-04-21 18:04** |

**验证**：
```python
# 加载索引后：
target = [c for c in chunks if 'Enzymatic twists' in c.paper_title]
# → target chunks: 0
```

目标论文 **根本不在向量索引里**。索引里只有 13 篇论文、70 个 chunk，而磁盘上有 6753 个 JSON。索引是 3 月 29 日构建的，之后新增的所有数据都没被嵌入向量化。

**代码层面原因**（`search/retriever.py:52-88`）：
```python
if not force and chunks_file.exists() and emb_file.exists():
    print("Loading existing index...")
    ...
    return
```
`JinaRetriever.build_index()` 看到 `chunks.pkl` / `embeddings.npy` 就直接 `return`，**不会做增量同步**。只要没人手动 `build_index(force=True)`，新增的 6700+ 篇论文就永远不会进索引。

这直接解释了"答案字段排不进 top 10 + 返回 10 篇不相干文献"：候选集里压根没有目标数据，向量相似度只能在 70 条黄酮/花青素等完全不相关的数据里硬挑 10 条。

---

### 🟡 问题 2：加论文标题为什么能找到？—— PubMed 兜底

看 `core/agent.py` 的工具调用逻辑：默认 `sources = ["pubmed", "gene_db"]`。

- 加论文标题后，LLM 更倾向于走 **`pubmed_search`**（或 `rag_search` 里的 pubmed 通道），用标题去 PubMed 联网查 —— PubMed 当然能找到 Nature Plants 的这篇论文；
- PubMed 返回的摘要包含 "stereo-divergent alkaloids in the Solanaceae"、"25S/25R"、"GAME8" 等关键词，reranker 把它排到前面；
- 用户以为是 "RAG 工作了"，实际是 **PubMed 帮忙兜底，本地基因库依然没命中**。

---

### 🟠 问题 3：Chunk 粒度太粗

即使现在跑 `build_index(force=True)` 重建，仍有以下隐患：

**(1) 单 chunk 把 30+ 字段全塞进 1 段文本**（`utils/data_loader.py:102-167`）：
```python
for key, value in gene.items():
    ...
    content_parts.append(f"{field_name}: {value_str}")
content = "\n".join(content_parts)
```
GAME8 的 chunk 包含 Gene_Accession_Number、EC_Number、Biosynthetic_Pathway、Metabolic_Step_Position、Terminal_Metabolite、Summary_Key_Findings_of_Core_Gene（500+ 字）、Other_Important_Info ……

jina-embeddings-v3 对长、多主题、半结构化文本做单一向量嵌入时会做"语义平均"，"25S/25R 立体化学"、"番茄/马铃薯/茄子" 等关键概念被其他 30 个字段稀释。用户 query 很精准（"25S/25R 构型"、"α-番茄碱"、"α-澳洲茄胺"），但要匹配的 chunk 里这些词只占 10% 不到。

**(2) 字段名被翻译为中文混入英文值**：
`translate.json` 把字段名翻译为中文后嵌入，而用户 query 是中文、chunk 内容是"中文字段名 + 英文值"的混合。`retrieval.passage` / `retrieval.query` 的跨语言匹配在混合场景下不稳定。

**(3) 无效 DOI 噪声**：
`10.1038@s41467-025-59290-4_nutri_plant_verified.json` 第 4 行 `"DOI": "NA"`，但 loader 仍把它拼进 chunk 头部 `DOI: NA`，对嵌入无帮助且引入噪声。

---

### 🟢 问题 4：没有做字段级切分 / 多向量

现状是"1 基因 = 1 chunk = 1 向量"。用户这个查询（构型 + 生物学功能）的答案主要在两个字段：

- `Terminal_Metabolite`：
  > *…determines 25S vs 25R aglycone isomers such as tomatidenol/tomatidine versus solasodine…*
- `Summary_Key_Findings_of_Core_Gene`：
  > *Tomato-like GAME8 enzymes generate mainly 25S products, whereas eggplant-like GAME8 enzymes generate 25R products.*

如果对每个高价值字段单独向量化（field-level chunk），这个查询的召回率会大幅提高。

---

## 三、修复建议（按成本/收益排序）

### 1. 立刻修复：重建索引（最小改动）
```bash
cd /data/haotianwu/biojson/rag
python -c "from search.retriever import JinaRetriever; r=JinaRetriever(); r.build_index(force=True)"
```
这一步应把 70 chunks 扩到 6000+ chunks，原测试问题立即有机会被召回。**注意提前估算 Jina embedding API 成本**（6000+ 文档 × 每文档 2-5k 字符）。

### 2. 短期：增量索引 + 监控
- 在 `build_index()` 里比较 `data_dir` 文件列表与 `chunks.pkl` 里已有 DOI / 文件集合，**只对新增/修改的文件嵌入**；
- 启动时日志：`len(chunks)` vs `len(list(DATA_DIR.glob('*_verified.json')))`，不一致就告警。

### 3. 中期：优化 chunk 粒度
按字段重要性/主题做分层切分：
- 高信息密度字段（`Summary_Key_Findings_of_Core_Gene`、`Terminal_Metabolite`、`Core_Phenotypic_Effect` 等）独立成 chunk；
- 每 chunk 在 metadata 里保留 `gene_name` + `doi`，检索后在 agent 层聚合回 gene；
- 详细方案见同目录下 `CHUNKER_IMPLEMENTATION_PLAN.md`。

### 4. 中期：query 端改写 / 扩展
在调 `gene_db_search` 前让小模型把用户自然语言 query 改写成"富关键词 query"（提取 "25S, 25R, α-tomatine, α-solasonine, GAME8, Solanaceae"），再做向量检索。用户手动加"参考 Nature Plants"本质上就是在做这件事 —— 让系统自动化。

### 5. 长期：混合检索（hybrid retrieval）
`gene_db_search` 目前是纯稠密向量检索。加一路 BM25 / 关键词召回（尤其对基因名、化合物名这类专有名词多的场景），两路合并后再 rerank，可以显著缓解"专有名词被语义平均掉"的问题。

---

## 四、一句话结论

**这不是 "RAG 检索排名靠后" 的问题，而是 "目标文档根本不在索引里" 的问题**。本地向量索引是 2026-03-29 构建的老索引，仅包含 70 条、13 篇论文；之后新增的 6700+ 篇论文（包括 Nature Plants 那篇）从未被嵌入。加论文标题后能找到答案，是因为 `rag_search` 的 **PubMed 兜底通道**替本地基因库擦了屁股。

---

## 五、关联文档

- **下一步完整 chunker 重构方案** → `CHUNKER_IMPLEMENTATION_PLAN.md`
- 现有向量检索模块 → `search/retriever.py`
- 现有 chunk 生成逻辑 → `utils/data_loader.py`
- 现有工具调用 Agent → `core/agent.py`
