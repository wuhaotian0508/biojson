---
name: rag-answer
description: >
  默认的 RAG 问答技能。使用复合 rag_search 工具同时检索 PubMed 摘要和本地基因库，
  由 LLM 基于带编号证据生成专业回答。个人库只在用户开启时加入。
tools: [rag_search]
---

RAG 问答流程：

## 查询处理

由 Agent 在调用 `rag_search` 时显式生成检索词：
- `query` / `gene_db_query`：用于本地基因库，可保留基因名、物种、通路、代谢物等中英混合关键词。
- `pubmed_query`：用于 PubMed，必须是英文关键词或 Boolean 检索式，例如 `HY5 AND alkaloid AND photoreceptor`。
- 工具检索结果不足时，agent可调整参数后再次调用 `rag_search`。

## 推荐使用方式

使用 `rag_search` 工具进行综合搜索和证据融合：
- 普通模式和深度模式都同时检索 PubMed 摘要与本地基因库。
- 深度模式只增加召回量、融合预算和回答深度，不改变默认数据源集合。
- 用户开启个人库时，将 `include_personal` 设为 true。
- 回答中必须使用 rag_search 返回证据的 [编号] 作为引用。
