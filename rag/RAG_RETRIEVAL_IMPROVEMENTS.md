# RAG 检索优化 — 后续改进方案交接文档

**创建时间**: 2026-04-23
**当前状态**: BM25 + Dense RRF 混合检索已上线（选项 C 已完成），本档面向"第三条 query 仍丢失"暴露出的**系统性**短板，给出通用改造方案。

---

## 0. 背景与当前成果

- **数据规模**: 6753 篇 verified JSON → 57858 chunks → Jina v3 1024-dim embeddings
- **已落地**:
  - 按论文结构路由的四套 chunker（plant / pathway / mixed / generic）+ 增量索引（sha256 + chunker_version）
  - `setsid + nohup` 守护进程 + embedding checkpoint（10 批 flush 一次）
  - BM25 倒排索引（`rag/index/bm25.pkl`）+ RRF 融合（`rrf_fuse`）
  - `JinaRetriever.hybrid_search()` 集成完成
- **Smoke test 结果**:
  - 长 query "25S/25R 构型 + α-番茄碱…" → GAME8 从 miss → **rank #2** ✅
  - "25S 构型与 25R 构型生物碱差异" → GAME8 从 miss → **rank #2** ✅
  - **"α-番茄碱与 α-澳洲茄胺的生物学功能" → 仍 miss** ❌ ← 本文档要解决的 case

---

## 1. 根因诊断（不是单点问题）

查看 GAME8 chunk（idx=2426, `chunk_type="gene"`, content 5082 字符）发现：

- chunk 内容**只有英文**: `α-tomatine`, `solasodine`, `tomatidenol`, `soladulcidine`
- 用户 query **只有中文**: "α-番茄碱", "α-澳洲茄胺"
- **BM25 永远匹配不上**：分词后两个语言的 token 完全不交集
- **Dense 向量也被稀释**：5082 字符里只有少量化合物词，语义被其他上下文拉平

这个现象不是 GAME8 独有，而是整个系统的**三类通用弱点**：

| # | 弱点 | 表现 | 影响面 |
|---|---|---|---|
| ① | **跨语言词汇鸿沟** | 文献是英文、JSON 抽取字段多为英文；用户 query 常为中文 | 全部中文 query × 英文文献 |
| ② | **Chunk 粒度不均** | generic chunker 单篇压成一个大 chunk，专有名词被稀释 | 所有落入 generic 分支的论文 |
| ③ | **Query 信息密度不足** | 用户原始 query 是自然语言问句；chunk 是事实性片段，分布失配 | 所有问答式 query |

**结论**：需要在 3 个层次上做通用改造，不应针对单个 query 打补丁。

---

## 2. 三层通用改造方案

### 方案 A — 索引侧 Chunk Enrichment（加"别名附录"）

**目标**: 让每个 chunk 都自带专有名词 + 双语同义词的浓缩索引区，同时强化 BM25（精确词）和 Dense（语义上下文）。

#### A1. 多来源 alias 抽取 pipeline

在 `utils/chunker/base.py` 的 `_postprocess` 阶段，对每个 chunk 做：

```
chunk.content →
  [1] 正则抽取   : 基因名(GAME8)、EC号、CYP*、化合物(α-tomatine)、
                   立体描述符(25S/25R)、蛋白家族(Cytochrome P450)
  [2] 字段抽取   : 从 chunk.source_fields 直接取
                   gene_name / gene_accession / enzyme_name /
                   primary_substrate / primary_product / end_products
  [3] 翻译映射   : 查 translate.json (现有) +
                   新增 bilingual_glossary.json（几百条领域高频词）
                   例: "α-tomatine" ↔ "α-番茄碱"
                       "solasodine"  ↔ "澳洲茄胺"
                       "steroidal alkaloid" ↔ "甾体生物碱"
  [4] 形态归一   : 大小写折叠、全半角、希腊字母同义(alpha↔α)

→ 在 chunk.content 末尾追加一段：
  "\n[aliases] GAME8 CYP72A208 α-tomatine α-番茄碱
                solasodine 澳洲茄胺 25S 25R ..."
```

**通用性**：
- 不 hard-code 任何基因/化合物名，全部从字段或正则自动来
- `bilingual_glossary` 只需维护领域高频术语（几百条），不逐词翻译
- 附录同时喂 BM25（新 token 精确匹配）和 Embedding（新上下文）→ 两路都强化

#### A2. 切分时保留别名密度

当前 `CHUNK_MAX_BODY_LEN=1500`，切分后子 chunk 可能完全丢掉专有名词。

**改造**: 切分时 `[aliases]` 附录**复制到每个子 chunk**（不切分），保证每段都有 anchor。

#### A3. 落地要点

- 文件: `utils/chunker/base.py::BaseChunker._postprocess`
- 需新建: `utils/chunker/alias_extractor.py`, `config/bilingual_glossary.json`
- 触发全量重建：修改后 `CHUNKER_VERSION` 升级 → 下次 `build_incremental()` 自动全量重建
  - embedding checkpoint 机制已就绪，中断可续
  - 估算成本：57858 chunks × Jina v3 ≈ 原重建的 1 倍时间（chunk 文本略长）

---

### 方案 B — Query 侧双向扩写

即使索引侧做了增强，query 本身可能过于口语化或单语，需要做扩写。

#### B1. 规则扩写（离线、零成本）

```python
def expand_query(q: str) -> List[str]:
    variants = [q]
    # 1. 双语 glossary 反查：中→英、英→中
    for zh, en in bilingual_glossary.items():
        if zh in q:
            variants.append(q.replace(zh, f"{zh} {en}"))
        if en.lower() in q.lower():
            variants.append(q + f" {zh}")
    # 2. 立体化学归一：
    #    "25S 构型" → 追加 "25S-configured", "(25S)-"
    # 3. 希腊字母互转：α ↔ alpha、β ↔ beta
    return variants
```

使用方式：多变体各跑一次检索，或拼接成一个增强 query 送入。

#### B2. LLM / HyDE 扩写（可选，按需触发）

使用小模型一次 call，把 query 改写为 3 条：

- **纯英文版本** — 对齐英文 chunk
- **专有名词版本** — 只保留基因/化合物/EC 号
- **HyDE 假设答案版本** — 让模型先"猜"一段 1-2 句话的回答，用作额外 query（假设答案的语言分布更接近 chunk 内容）

触发策略：当 `hybrid_search` 返回的 top-1 RRF score < 阈值（经验值 0.015）时才触发，避免每 query 都付 LLM 成本。

#### B3. 落地要点

- 文件: 新建 `search/query_expander.py`
- 与 `hybrid_search()` 集成：
  ```python
  queries = expand_query(raw_q)
  ranked_lists = [self._dense_search(q, dense_k) for q in queries]
  ranked_lists.append(self._bm25_search(raw_q, bm25_k))
  return rrf_fuse(*ranked_lists, ...)
  ```

---

### 方案 C — 检索侧三路融合 + Cross-Encoder 重排

升级当前 2 路 hybrid 为 3~4 路召回 + 重排。

```
query → expand →
    ├─ dense(query)         [原 query 稠密向量]
    ├─ dense(query_en)      [扩写后的英文 query 稠密向量]
    ├─ BM25(multilang)      [中英双 token 的 BM25]
    └─ BM25(aliases_only)   [只保留专有名词做精确召回]
            ↓
    RRF(4 路，top-200) → top-50
            ↓
    Cross-Encoder Rerank (jina-reranker-v2) → top-10
```

#### C1. Cross-Encoder Rerank 的价值

- 与 bi-encoder（当前 embedding）不同，cross-encoder 做 query × chunk 的**联合编码**，天生能处理跨语言 + 长 chunk 语义稀释
- Jina 官方有 `jina-reranker-v2-base-multilingual`，支持中英混合，128 文档批打分
- 只对 top-50 候选重排，延迟增加约 200~500ms，可接受

#### C2. 落地要点

- 新建: `search/reranker.py`
  ```python
  def rerank(query: str, candidates: List[Tuple[Chunk, float]],
             top_k: int = 10) -> List[Tuple[Chunk, float]]:
      """调用 Jina reranker API，对候选做 cross-encoder 重排"""
      ...
  ```
- 改造 `hybrid_search(rerank: bool = False)` 增加开关
- API endpoint: `https://api.jina.ai/v1/rerank`（与 embedding 同 key）

---

## 3. 三层方案对比与推荐组合

| 层 | 解决的问题 | 代价 | 覆盖面 | 推荐度 |
|---|---|---|---|---|
| **A 索引 enrichment** | 词汇鸿沟 + chunk 粒度 | 中（需重跑 chunker，可增量 checkpoint） | 全部 query | ★★★★ 影响长远 |
| **B1 规则扩写** | 中英 query 映射 | 极低（离线） | 双语 query | ★★★★ |
| **B2 LLM/HyDE** | 口语化 query | 1 次小模型 call/query（可条件触发） | 自然语言 query | ★★ 可选 |
| **C Cross-Encoder Rerank** | 长 chunk 稀释 + 跨语言语义 | +200~500ms/query | **全部 query** | ★★★★★ 最通用 |

### 如果只做一件事

→ **做方案 C（Cross-Encoder Rerank）**

理由：
1. 不依赖词表完整性
2. 不需重建索引
3. 对任何语言、任何粒度 chunk 都生效
4. 验证最快（30 分钟可跑通）

### 最佳组合

**A + B1 + C** 三层互补，完全不 hard-code 任何基因/化合物名，可沉淀成基础设施。

---

## 4. 落地路线图（由易到难）

### Phase 1 — 立刻可做（~30 分钟）

**目标**: 验证 cross-encoder rerank 是否能单独解决第三条 query

- [ ] 新建 `rag/search/reranker.py`，封装 Jina rerank API（带重试）
- [ ] 给 `JinaRetriever.hybrid_search()` 加 `rerank: bool = False` 参数
- [ ] 扩展 `scripts/smoke_test_hybrid.py` 对比 `hybrid` vs `hybrid+rerank`
- [ ] 跑 smoke test，确认"α-番茄碱与 α-澳洲茄胺"能否命中 top-10

### Phase 2 — 本周可做（~半天）

**目标**: Query 规则扩写，解决大部分中英 query 映射

- [ ] 收集/构建 `config/bilingual_glossary.json`（初版从 `translate.json` 导入 + 手工补充高频词）
- [ ] 新建 `rag/search/query_expander.py`
- [ ] 改造 `hybrid_search()` 支持多 query 变体 RRF 融合
- [ ] 扩充 smoke test case 集

### Phase 3 — 下次 chunker 升级时（~1 天 + 重建时间）

**目标**: 把双语别名附录沉淀到 chunk 中，一次投入长期受益

- [ ] 新建 `rag/utils/chunker/alias_extractor.py`
- [ ] 改造 `BaseChunker._postprocess` 追加 `[aliases]` 附录
- [ ] 改造切分逻辑：附录复制到每个子 chunk
- [ ] 升级 `CHUNKER_VERSION = "v3.2026-xx"`
- [ ] 运行增量重建（会触发全量，但 checkpoint 机制可断点续传）
  ```bash
  bash rag/scripts/run_rebuild_daemon.sh --force
  ```
- [ ] 跑完整 smoke test 验证所有历史 case + 新增 case 不回退

### Phase 4 — 可选进阶

- [ ] LLM / HyDE 扩写（条件触发：top-1 score < 阈值）
- [ ] 建立 query 回归测试集（≥20 条中英混合 query，每条标注期望命中基因）
- [ ] 在 `scripts/` 下增加 `eval_retrieval.py`，输出 MRR/Recall@k 等指标

---

## 5. 相关文件速查

| 用途 | 路径 |
|---|---|
| 混合检索主入口 | `rag/search/retriever.py::JinaRetriever.hybrid_search` |
| BM25 模块 | `rag/search/bm25_retriever.py` |
| Chunker 基类（未来 enrichment 的修改点） | `rag/utils/chunker/base.py` |
| 现有翻译词典 | `rag/utils/chunker/translate.json` |
| 增量索引 + 监控 | `rag/utils/indexer.py` |
| 全量重建入口 | `rag/scripts/rebuild_index.py` |
| 后台守护启动 | `rag/scripts/run_rebuild_daemon.sh` |
| BM25 一次性构建 | `rag/scripts/build_bm25_index.py` |
| Hybrid smoke test | `rag/scripts/smoke_test_hybrid.py` |
| 本文档 | `rag/RAG_RETRIEVAL_IMPROVEMENTS.md` |
| 前序问题分析 | `rag/RAG_RETRIEVAL_ISSUES.md` |
| Chunker 架构 | `rag/CHUNKER_IMPLEMENTATION_PLAN.md` |

---

## 6. 风险与注意事项

- **CHUNKER_VERSION 升级 = 全量重建**：会消耗 Jina API 配额；已有 checkpoint 机制，中断可续，但需留足时间/额度
- **Rerank API 配额**：每 query 多 1 次 rerank call，高 QPS 场景需评估成本；建议只对 top-50 候选 rerank
- **bilingual_glossary 维护**：不要试图全量翻译，只覆盖"高频领域术语"（经验值 200-500 条）
- **HyDE 扩写的副作用**：模型"猜"的答案可能把 query 带偏，建议加置信度阈值 + 人工审查一批样本后再默认开启
- **评估基线**：每次做一层改造前，先用固定 query 集跑一轮 baseline，避免"感觉变好了"的主观判断

---

## 7. 一句话总结

> 单条 query 的 miss 不要单独修，要**从"索引-查询-检索"三层分别抽取可复用机制**：
> - 索引加双语别名（治根）
> - 查询做规则扩写（廉价）
> - 检索加 cross-encoder rerank（通用最强）
>
> 优先级：**C > A > B1 > B2**；最小可行改动是先做 C。
