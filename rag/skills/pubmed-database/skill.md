---
name: pubmed-database
description: >
  搜索 PubMed 生物医学文献数据库，支持高级检索语法、MeSH 术语、
  字段限定搜索和系统性文献综述。当用户询问基因功能、代谢通路、
  作物育种相关文献时自动触发。
tools: [pubmed_search]
---

# PubMed 文献搜索技能

使用 `pubmed_search` 工具搜索 NCBI PubMed 数据库，获取生物医学文献的标题、摘要、期刊和链接。

## 使用时机

- 用户询问特定基因、蛋白质、代谢通路的研究文献
- 用户需要查找作物营养代谢相关的最新进展
- 用户要求文献综述或研究证据支持
- 涉及 CRISPR、基因编辑、转基因等生物技术主题

## 搜索策略

### 1. 构建英文查询

PubMed 以英文文献为主，查询词应使用英文。工具会自动将中文翻译为英文。

### 2. 使用精确的搜索词

| 搜索目标 | 推荐查询模式 | 示例 |
|---------|-------------|------|
| 特定基因功能 | `基因名 + 功能关键词 + 物种` | `OsNAS2 iron biofortification rice` |
| 代谢通路 | `通路名 + crop/plant` | `carotenoid biosynthesis pathway maize` |
| 基因编辑 | `CRISPR + 基因名 + 物种` | `CRISPR Cas9 GmFAD2 soybean` |
| 营养强化 | `biofortification + 营养素 + 作物` | `biofortification vitamin A wheat` |
| 综述文献 | `关键词 + review` | `selenium metabolism plant review` |
| 特定作者 | `作者名 + 研究方向` | `Zhang H CRISPR rice nutrition` |

### 3. 使用 PubMed 高级语法（传入 pubmed_search 的 query 参数）

- **MeSH 术语**: `vitamin C[MeSH]` — 使用 MeSH 受控词汇，自动包含下位词
- **字段限定**: `CRISPR[Title]` — 限定标题搜索；`Zhang[Author]`
- **布尔运算**: `rice AND (iron OR zinc) AND biofortification`
- **日期限定**: `2020:2024[Date - Publication]` — 限定发表年份
- **文献类型**: `review[Publication Type]` — 限定综述文章

### 4. 分步搜索策略

对于复杂问题，分多次搜索不同角度：

1. **先搜基因名 + 功能** — 获取直接相关文献
2. **再搜通路名 + 物种** — 补充通路上下游信息
3. **最后搜综述** — 获取领域全貌

### 5. PICO 框架（系统性综述）

对于需要全面文献检索的问题：

- **P**opulation: 目标物种/作物（如 rice, wheat, maize）
- **I**ntervention: 干预手段（如 CRISPR editing, overexpression）
- **C**omparison: 对照组（如 wild type, untreated）
- **O**utcome: 预期结果（如 increased iron content, enhanced yield）

## 结果处理

- 工具返回每篇文献的标题、期刊、PMID 和摘要
- 在回答中使用 [1] [2] 等编号引用文献
- 优先引用高影响力期刊（Nature, Science, Plant Cell, PNAS 等）
- 优先引用近 5 年的研究成果
- 注意区分实验验证的结论和关联性推测

## 常用查询模板

```
# 维生素代谢基因
vitamin E tocopherol biosynthesis gene crop

# 矿物质转运蛋白
iron transporter gene rice biofortification

# 氨基酸代谢
lysine biosynthesis regulation maize kernel

# 类胡萝卜素通路
carotenoid pathway gene golden rice beta-carotene

# 基因编辑应用
CRISPR genome editing nutritional quality crop improvement
```
