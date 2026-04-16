---
name: rag-answer
description: >
  默认的 RAG 问答技能。搜索 PubMed 文献和基因数据库，
  由 LLM 生成专业回答。普通模式搜索 PubMed，深度模式额外检索基因库。
tools: [rag_search, pubmed_search, gene_db_search, personal_lib_search, design_crispr_experiment]
---

RAG 问答流程：

推荐使用 `rag_search` 工具进行综合搜索+重排：
- 普通模式：`rag_search(query, sources=["pubmed"])`
- 深度模式：`rag_search(query, sources=["pubmed", "gene_db"])`
- 开启个人库：在 sources 中加入 `"personal_lib"`

也可使用单独工具进行针对性搜索：
- `pubmed_search`: 单独搜索 PubMed 文献
- `gene_db_search`: 单独检索基因数据库
- `personal_lib_search`: 单独检索个人知识库
