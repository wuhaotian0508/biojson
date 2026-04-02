---
name: crispr-experiment
description: >
  当回答中明确建议对某个具体基因进行 CRISPR 编辑、敲除、过表达或遗传转化实验时，
  调用此技能自动生成完整的实验方案 SOP。
version: 1.0.0
tags: [crispr, experiment, gene-editing, sop]
---

# CRISPR 实验方案自动生成

## 触发条件
回答中明确建议对具体基因进行编辑/敲除/过表达/转基因操作时触发。
仅综述中提到基因编辑技术但无具体基因建议时不触发。

## 执行流程
调用 run_crispr_pipeline 工具，传入基因列表。后端自动执行：

1. gene2accession.py.py — 查询 NCBI 获取基因 accession
2. accession2sequence.py.py — 下载 FASTA 基因序列
3. crispr_target.py — 设计 CRISPR 靶点
4. experiment_design.py — 基于模板生成实验方案 SOP

所有脚本位于 rag/分析流程/ 目录。
