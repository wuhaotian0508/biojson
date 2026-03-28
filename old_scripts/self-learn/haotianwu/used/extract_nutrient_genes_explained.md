# extract_nutrient_genes 工具函数详解

这是一个用于从科学论文中提取作物营养代谢基因信息的函数定义。

## 基本结构

```python
EXTRACT_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_nutrient_genes",
        "description": "Extract crop nutrient metabolism gene information from a scientific paper. "
                       "Extract ALL genes that are directly experimentally validated in the Results section. "
                       "If information is not found, use 'NA'.",
        ...
    }
}
```

## 各部分解释

### 1. 函数名称
- **name**: `extract_nutrient_genes` - 从论文中提取营养代谢基因信息

### 2. 描述 (description)
- 提取对象：作物营养代谢相关的基因信息
- 提取来源：论文的 Results 部分
- 提取要求：仅提取**直接经过实验验证**的基因
- 缺失处理：如果信息找不到，使用 `'NA'`

### 3. 参数定义 (parameters)

| 参数 | 类型 | 说明 |
|------|------|------|
| **Title** | string | 论文的完整标题 |
| **Journal** | string | 期刊名称 |
| **DOI** | string | 纯DOI字符串（不带URL前缀） |
| **Genes** | array | 基因对象数组，包含关键基因信息 |

### 4. Genes 数组
- 每个基因对象包含 `GENE_PROPERTIES` 中定义的属性
- 这些基因应该是影响最终营养产物的酶或调控因子

## 用途

这个工具通常用于：
1. 构建作物营养代谢基因数据库
2. 文献挖掘，分析基因-营养物质的关系
3. 自动化从大量论文中提取基因信息
