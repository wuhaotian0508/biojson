---
name: rag-answer
description: >
  默认的 RAG 问答技能。使用复合 rag_search 工具同时检索 PubMed 摘要和本地基因库，
  由 LLM 基于带编号证据生成专业回答。个人库只在用户开启时加入。
tools: [rag_search]
---

RAG 问答流程：

## 查询处理

系统会自动使用 LLM 提取查询中的关键生物学术语并翻译成英文，无需手动翻译。

## 推荐使用方式

使用 `rag_search` 工具进行综合搜索和证据融合：
- 普通模式和深度模式都同时检索 PubMed 摘要与本地基因库。
- 深度模式只增加召回量、融合预算和回答深度，不改变默认数据源集合。
- 用户开启个人库时，将 `include_personal` 设为 true。
- 回答中必须使用 rag_search 返回证据的 [编号] 作为引用。
