"""
数据加载器 - 从 JSON 文件加载基因数据并生成 chunk
"""
import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
import config


@dataclass
class GeneChunk:
    """基因信息块"""
    gene_name: str          # 基因名称
    paper_title: str        # 文章标题
    journal: str            # 期刊
    doi: str                # DOI
    gene_type: str          # 基因类型 (Pathway_Genes/Regulation_Genes/Common_Genes)
    content: str            # 格式化的基因信息文本
    metadata: Dict[str, Any]  # 原始基因数据


class DataLoader:
    """数据加载器"""

    def __init__(self, data_dir: Path = config.DATA_DIR):
        self.data_dir = data_dir
        self.translation = self._load_translation()

    def _load_translation(self) -> Dict[str, str]:
        """加载字段翻译映射"""
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
        """创建基因信息块"""
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
