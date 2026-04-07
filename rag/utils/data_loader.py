"""
数据加载器 — 从验证后的 JSON 文件加载基因数据并生成 GeneChunk

职责：
  1. 扫描 DATA_DIR 下所有 *_nutri_plant_verified.json 文件
  2. 解析三种基因类型：Pathway_Genes / Regulation_Genes / Common_Genes
  3. 将每个基因的字段格式化为可检索的纯文本 chunk
  4. 使用 translate.json 将英文字段名翻译为中文（可选）

输出的 GeneChunk 列表用于构建向量索引（JinaRetriever / SimpleRetriever）。
"""
import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
import config


@dataclass
class GeneChunk:
    """
    基因信息块 — 向量检索的基本单元。

    每个 GeneChunk 对应一篇论文中的一个基因，
    content 字段包含该基因的所有结构化信息（已格式化为纯文本）。
    """
    gene_name: str              # 基因名称，如 "GmFAD2"
    paper_title: str            # 来源论文标题
    journal: str                # 来源期刊
    doi: str                    # 论文 DOI
    gene_type: str              # 基因类别 (Pathway_Genes/Regulation_Genes/Common_Genes)
    content: str                # 格式化的纯文本（用于嵌入和检索）
    metadata: Dict[str, Any]    # 原始基因 JSON 数据（保留所有字段）


class DataLoader:
    """
    基因数据加载器 — 从 JSON 文件批量读取基因信息并生成 GeneChunk。

    数据来源：extractor 模块输出的 *_nutri_plant_verified.json 文件，
    每个文件包含一篇论文中提取的所有基因数据。
    """

    def __init__(self, data_dir: Path = config.DATA_DIR):
        """
        参数:
            data_dir: 基因 JSON 数据目录（默认 config.DATA_DIR）
        """
        self.data_dir = data_dir
        self.translation = self._load_translation()  # 字段名 英→中 翻译表

    def _load_translation(self) -> Dict[str, str]:
        """
        加载字段名翻译映射（英文字段名 → 中文显示名）。

        翻译文件 translate.json 位于 rag/ 目录下，格式：
          {"Gene_Name": "基因名称", "Species": "物种", ...}

        若文件不存在，返回空字典（字段名将以英文原名显示）。
        """
        translate_file = config.PROJECT_ROOT / "translate.json"
        if translate_file.exists():
            with open(translate_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def load_all_genes(self) -> List[GeneChunk]:
        """加载所有基因数据"""
        chunks = []
        json_files = list(self.data_dir.glob("*_nutri_plant_verified.json"))

        print(f"找到 {len(json_files)} 个数据文件")

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                paper_title = data.get("Title", "Unknown")
                journal = data.get("Journal", "Unknown")
                doi = data.get("DOI", "Unknown")

                # 处理三种基因类型
                for gene_type in ["Pathway_Genes", "Regulation_Genes", "Common_Genes"]:
                    genes = data.get(gene_type, [])
                    for gene in genes:
                        chunk = self._create_gene_chunk(
                            gene=gene,
                            paper_title=paper_title,
                            journal=journal,
                            doi=doi,
                            gene_type=gene_type
                        )
                        chunks.append(chunk)

            except Exception as e:
                print(f"处理文件 {json_file} 时出错: {e}")

        print(f"总共加载了 {len(chunks)} 个基因")
        return chunks

    def _create_gene_chunk(self, gene: Dict, paper_title: str,
                          journal: str, doi: str, gene_type: str) -> GeneChunk:
        """
        将单个基因的 JSON 数据格式化为 GeneChunk。

        格式化逻辑：
          1. 头部固定字段：基因名、文章、期刊、DOI、基因类型
          2. 遍历基因的所有字段，跳过 NA/空值
          3. 字段名使用翻译表转换为中文
          4. 列表类型的值用 "; " 连接

        参数:
            gene:        单个基因的 JSON 字典
            paper_title: 来源论文标题
            journal:     来源期刊名
            doi:         论文 DOI
            gene_type:   基因类别键名

        返回:
            GeneChunk 实例
        """
        gene_name = gene.get("Gene_Name", "Unknown")

        # 格式化基因信息
        content_parts = [
            f"基因名称: {gene_name}",
            f"文章: {paper_title}",
            f"期刊: {journal}",
            f"DOI: {doi}",
            f"基因类型: {self._translate_gene_type(gene_type)}",
            ""
        ]

        # 添加基因详细信息
        for key, value in gene.items():
            if key == "Gene_Name":
                continue

            # 跳过 NA 和空值
            if value in [None, "NA", "", []]:
                continue

            # 翻译字段名
            field_name = self.translation.get(key, key)

            # 格式化值
            if isinstance(value, list):
                value_str = "; ".join(str(v) for v in value if v and v != "NA")
                if not value_str:
                    continue
            else:
                value_str = str(value)

            content_parts.append(f"{field_name}: {value_str}")

        content = "\n".join(content_parts)

        return GeneChunk(
            gene_name=gene_name,
            paper_title=paper_title,
            journal=journal,
            doi=doi,
            gene_type=gene_type,
            content=content,
            metadata=gene
        )

    def _translate_gene_type(self, gene_type: str) -> str:
        """翻译基因类型"""
        mapping = {
            "Pathway_Genes": "代谢途径基因",
            "Regulation_Genes": "调控基因",
            "Common_Genes": "通用基因"
        }
        return mapping.get(gene_type, gene_type)


if __name__ == "__main__":
    loader = DataLoader()
    chunks = loader.load_all_genes()
    print(f"加载了 {len(chunks)} 个基因 chunk")

    # 显示第一个 chunk 示例
    if chunks:
        print("\n示例 chunk:")
        print(chunks[0].content[:500])
