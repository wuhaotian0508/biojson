"""
CRISPR 实验方案 pipeline 单元测试

测试内容：
1. experiment_design: SOP 模板占位符替换是否正确
2. extract_selected_genes_with_llm: 为选定基因名解析物种
"""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
RAG_DIR = ROOT / "rag"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(RAG_DIR))

# ---- 导入新路径下的模块 ----
from rag.skills.crispr_experiment.experiment_design import run_experiment_design
from rag.skills.crispr_experiment.pipeline import ExperimentPipeline


def test_run_experiment_design_replaces_reverse_complement_placeholder(tmp_path):
    """
    测试 SOP 模板中的占位符是否被正确替换：
    - _gene_accession_ → accession 编号
    - _sequence_ → 正向靶点序列
    - _sequence_rt_ / _sequence_rc_ → 反向互补序列
    - _PAM_ → PAM 序列
    """
    # ---- 构造模拟的 CRISPR 靶点 TSV 文件 ----
    target_file = tmp_path / "crispr_target_recommended.txt"
    target_file.write_text(
        "\t".join([
            "Seq_name", "On_score", "Target_number",
            "Sequence", "PAM", "Region", "%GC", "Sequence_RC",
        ])
        + "\n"
        + "\t".join([
            "AB029261.1", "0.91", "3",
            "GGCTAAGGAA", "GGG", "exon", "55", "TTCCTTAGCC",
        ])
        + "\n",
        encoding="utf-8",
    )

    # ---- 调用独立函数（不再是 pipeline 方法） ----
    sops = run_experiment_design(target_file, tmp_path)

    output = sops["AB029261.1"]
    output_file = tmp_path / "CRISPR_SpCas9_Gene_Editing_AB029261.1.txt"

    # ---- 验证文件生成 ----
    assert output_file.exists()
    # ---- 验证占位符被正确替换 ----
    assert "NCBI GenBank登录号（AB029261.1）" in output
    assert "正向oligo: 5'-GCAG-[GGCTAAGGAA]-3'" in output
    assert "反向oligo: 5'-AAAC-[TTCCTTAGCC]-3'" in output
    # ---- 验证无残留占位符 ----
    assert "_sequence_rt_" not in output
    assert "rt_]-3'" not in output


def test_pipeline_cleanup(tmp_path):
    """测试 cleanup() 方法能正确清理临时目录"""
    pipeline = ExperimentPipeline.__new__(ExperimentPipeline)
    pipeline.work_dir = tmp_path / "test_work"
    pipeline.work_dir.mkdir()
    # 创建一些临时文件
    (pipeline.work_dir / "test.txt").write_text("test", encoding="utf-8")

    pipeline.cleanup()

    assert not pipeline.work_dir.exists()
