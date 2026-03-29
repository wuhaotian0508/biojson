"""数据加载和预处理模块"""
import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class GeneChunk:
    """基因信息切片，用于检索"""
    chunk_id: str
    text: str                # 用于检索的文本
    gene_name: str           # 基因名
    article_title: str       # 文章标题
    journal: str
    doi: str
    species: str
    category: str            # Plant/Animal/Microbial
    metadata: Dict[str, Any] # 完整的基因字段

def load_json_files(data_dir: Path) -> List[Dict]:
    """加载所有JSON文件"""
    files = list(data_dir.glob("*.json"))
    data = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data.append(json.load(fp))
        except Exception as e:
            print(f"Error loading {f}: {e}")
    return data

def gene_to_searchable_text(gene: Dict, article_title: str) -> str:
    """将基因信息转换为可检索的文本"""
    parts = []

    # 核心字段
    if gene.get("Gene_Name"):
        parts.append(f"基因名: {gene['Gene_Name']}")
    if gene.get("Species_Latin_Name"):
        parts.append(f"物种: {gene['Species_Latin_Name']}")
    if gene.get("Protein_Family_or_Domain"):
        parts.append(f"蛋白家族/结构域: {gene['Protein_Family_or_Domain']}")

    # 功能相关
    if gene.get("Core_Phenotypic_Effect"):
        parts.append(f"核心表型效应: {gene['Core_Phenotypic_Effect']}")
    if gene.get("Regulatory_Mechanism"):
        parts.append(f"调控机制: {gene['Regulatory_Mechanism']}")
    if gene.get("Regulatory_Pathway"):
        parts.append(f"调控通路: {gene['Regulatory_Pathway']}")
    if gene.get("Biosynthetic_Pathway"):
        parts.append(f"生物合成通路: {gene['Biosynthetic_Pathway']}")

    # 互作和调控
    if gene.get("Interacting_Proteins"):
        parts.append(f"互作蛋白: {gene['Interacting_Proteins']}")
    if gene.get("Upstream_or_Downstream_Regulation"):
        parts.append(f"上下游调控: {gene['Upstream_or_Downstream_Regulation']}")

    # 研究信息
    if gene.get("Research_Topic"):
        parts.append(f"研究主题: {gene['Research_Topic']}")
    if gene.get("Trait_Category"):
        parts.append(f"性状类别: {gene['Trait_Category']}")
    if gene.get("Key_Environment_or_Treatment_Factor"):
        parts.append(f"关键环境/处理因素: {gene['Key_Environment_or_Treatment_Factor']}")

    # 实验验证
    if gene.get("Core_Validation_Method"):
        parts.append(f"核心验证方法: {gene['Core_Validation_Method']}")
    if gene.get("Experimental_Methods"):
        parts.append(f"实验方法: {gene['Experimental_Methods']}")

    # 育种价值
    if gene.get("Breeding_Application_Value"):
        parts.append(f"育种应用价值: {gene['Breeding_Application_Value']}")

    # 关键发现
    if gene.get("Summary_key_Findings_of_Core_Gene"):
        parts.append(f"关键发现: {gene['Summary_key_Findings_of_Core_Gene']}")

    return "\n".join(parts)

def process_all_data(data_dir: Path) -> List[GeneChunk]:
    """处理所有数据，生成检索用的切片"""
    all_chunks = []
    raw_data = load_json_files(data_dir)

    for doc in raw_data:
        title = doc.get("Title", "Unknown")
        journal = doc.get("Journal", "Unknown")
        doi = doc.get("DOI", "")

        # 处理各类基因
        for category, key in [("Plant", "Plant_Genes"),
                              ("Animal", "Animal_Genes"),
                              ("Microbial", "Microbial_Genes")]:
            genes = doc.get(key, [])
            for i, gene in enumerate(genes):
                gene_name = gene.get("Gene_Name", f"Unknown_{i}")
                species = gene.get("Species_Latin_Name", gene.get("Species", "Unknown"))

                # 生成可检索文本
                text = gene_to_searchable_text(gene, title)

                chunk = GeneChunk(
                    chunk_id=f"{doi}_{gene_name}_{i}",
                    text=text,
                    gene_name=gene_name,
                    article_title=title,
                    journal=journal,
                    doi=doi,
                    species=species,
                    category=category,
                    metadata=gene
                )
                all_chunks.append(chunk)

    print(f"Processed {len(raw_data)} articles, {len(all_chunks)} gene chunks")
    return all_chunks

if __name__ == "__main__":
    from config import DATA_DIR
    chunks = process_all_data(DATA_DIR)
    print(f"\nSample chunk:")
    print(f"  Gene: {chunks[0].gene_name}")
    print(f"  Article: {chunks[0].article_title}")
    print(f"  Text preview: {chunks[0].text[:200]}...")
