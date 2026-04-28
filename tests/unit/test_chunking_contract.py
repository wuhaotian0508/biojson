from __future__ import annotations

import inspect


def test_chunk_paper_routes_mixed_gene_paper_without_legacy_utils_imports():
    from nutrimaster.rag.gene_index import GeneChunk, chunk_paper
    import nutrimaster.rag.gene_index as chunking

    source = inspect.getsource(chunking)
    assert "utils.chunk" not in source
    assert "utils.data_loader" not in source

    chunks = chunk_paper(
        {
            "Title": "Anthocyanin tomato",
            "Journal": "Nature Biotechnology",
            "DOI": "10.1038/nbt.1506",
            "Common_Genes": [
                {"Gene_Name": "PAL1", "Enzyme_Name": "phenylalanine ammonia lyase"},
                {"Gene_Name": "F3H", "Enzyme_Name": "flavanone 3-hydroxylase"},
                {"Gene_Name": "DFR", "Enzyme_Name": "dihydroflavonol 4-reductase"},
            ],
            "Pathway_Genes": [
                {
                    "Gene_Name": "CHS",
                    "Primary_Substrate": "p-coumaroyl-CoA",
                    "Primary_Product": "chalcone",
                    "Biosynthetic_Pathway": "anthocyanin biosynthesis",
                    "Core_Phenotypic_Effect": "increases anthocyanin pathway flux and provides a long enough functional description for chunk generation",
                }
            ],
            "Regulation_Genes": [
                {
                    "Gene_Name": "Del",
                    "Regulator_Type": "transcription factor",
                    "Primary_Regulatory_Targets": "CHS; DFR; ANS; F3H; F3'H; F3'5'H; anthocyanin transporter genes",
                    "Regulatory_Effect_on_Target_Genes": "activates anthocyanin biosynthesis, modification, and transport genes strongly in tomato fruit",
                    "Terminal_Metabolite": "anthocyanins",
                    "Core_Phenotypic_Effect": "purple tomato fruit",
                }
            ],
        }
    )

    assert all(isinstance(chunk, GeneChunk) for chunk in chunks)
    assert {chunk.chunk_type for chunk in chunks} >= {
        "paper_overview",
        "regulatory_network",
        "pathway_gene",
        "regulation_gene",
    }
    assert {chunk.relations["__router__"] for chunk in chunks} == {"mixed_bucket"}


def test_chunk_paper_generic_fallback_emits_gene_chunk():
    from nutrimaster.rag.gene_index import chunk_paper

    chunks = chunk_paper(
        {
            "Title": "Lycopene tomato",
            "Journal": "Plant Cell",
            "DOI": "10.example/lycopene",
            "Common_Genes": [
                {
                    "Gene_Name": "PSY1",
                    "Species": "Tomato",
                    "Summary_Key_Findings_of_Core_Gene": "PSY1 controls carotenoid accumulation in fruit.",
                }
            ],
        }
    )

    assert len(chunks) == 1
    assert chunks[0].gene_name == "PSY1"
    assert chunks[0].gene_type == "Common_Genes"
    assert chunks[0].chunk_type == "gene"
