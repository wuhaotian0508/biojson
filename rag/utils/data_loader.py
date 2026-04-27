"""
数据加载器 — 从验证后的 JSON 文件加载基因数据并生成 GeneChunk

职责：
  1. 扫描 DATA_DIR 下所有 *_nutri_plant_verified.json 文件
  2. 通过 utils.chunker.chunk_paper() 对每篇 paper 生成 chunk 列表
  3. 将 chunk 扁平化为 GeneChunk 供向量索引使用

说明：
  - 原 _create_gene_chunk 的"单 gene = 单 chunk"逻辑已迁移为 GenericChunker
    并由 PaperTypeRouter 路由至对应分型 chunker（plant_genes / pathway_chain
    / mixed_bucket / generic）。
  - GeneChunk 定义已移至 utils.chunk_types，此处 re-export 保持向后兼容。
"""
import json
from pathlib import Path
from typing import List

import core.config as config
from utils.chunk_types import GeneChunk            # 保持向后兼容的 re-export
from utils.chunker import chunk_paper


class DataLoader:
    """
    基因数据加载器 — 从 JSON 文件批量读取并调用 chunker 生成 GeneChunk。
    """

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or config.DATA_DIR

    def load_all_genes(self) -> List[GeneChunk]:
        """加载所有基因数据（调用新 chunker 路由）。"""
        chunks: List[GeneChunk] = []
        json_files = list(self.data_dir.glob("*_nutri_plant_verified.json"))

        print(f"找到 {len(json_files)} 个数据文件")

        router_stats = {}  # 路由分布统计
        chunk_type_stats = {}

        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                paper_chunks = chunk_paper(data)
                chunks.extend(paper_chunks)
                # 记录路由分布
                for c in paper_chunks:
                    r = c.relations.get("__router__", "unknown")
                    router_stats[r] = router_stats.get(r, 0) + 1
                    chunk_type_stats[c.chunk_type] = chunk_type_stats.get(c.chunk_type, 0) + 1
            except Exception as e:
                print(f"处理文件 {json_file.name} 时出错: {e}")

        print(f"总共生成 {len(chunks)} 个 chunk")
        print(f"  路由分布: {router_stats}")
        print(f"  chunk_type 分布: {chunk_type_stats}")
        return chunks

    def load_paper(self, json_file: Path) -> List[GeneChunk]:
        """加载单篇 paper 的 chunk（用于增量索引）。"""
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return chunk_paper(data)


if __name__ == "__main__":
    loader = DataLoader()
    chunks = loader.load_all_genes()
    print(f"加载了 {len(chunks)} 个 chunk")
    if chunks:
        print("\n示例 chunk:")
        print(f"chunk_type = {chunks[0].chunk_type}")
        print(chunks[0].content[:500])
