from __future__ import annotations

import json


def test_verified_gene_repository_loads_paper_and_canonical_genes(tmp_path):
    data_file = tmp_path / "paper_nutri_plant_verified.json"
    data_file.write_text(
        json.dumps(
            {
                "Title": "Anthocyanin tomato",
                "Journal": "Nature Biotechnology",
                "DOI": "10.1038/nbt.1506",
                "Pathway_Genes": [
                    {
                        "Gene_Name": "CHS",
                        "Species_Latin_Name": "Solanum lycopersicum",
                        "Terminal_Metabolite": "anthocyanins",
                    }
                ],
                "Regulation_Genes": [
                    {
                        "Gene_Name": "Del",
                        "Regulator_Type": "transcription factor",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    from domain import GeneBucket
    from storage import VerifiedGeneRepository

    paper = VerifiedGeneRepository(tmp_path).load_paper(data_file)

    assert paper.title == "Anthocyanin tomato"
    assert paper.journal == "Nature Biotechnology"
    assert paper.doi == "10.1038/nbt.1506"
    assert [(gene.name, gene.bucket) for gene in paper.genes] == [
        ("CHS", GeneBucket.PATHWAY),
        ("Del", GeneBucket.REGULATION),
    ]
    assert paper.genes[0].field("Terminal_Metabolite") == "anthocyanins"
    assert paper.genes[1].field("Regulator_Type") == "transcription factor"


def test_verified_gene_repository_iterates_matching_files_in_stable_order(tmp_path):
    (tmp_path / "ignore.json").write_text("{}", encoding="utf-8")
    for name, title in [
        ("b_nutri_plant_verified.json", "B"),
        ("a_nutri_plant_verified.json", "A"),
    ]:
        (tmp_path / name).write_text(
            json.dumps({"Title": title, "Journal": "J", "DOI": title}),
            encoding="utf-8",
        )

    from storage import VerifiedGeneRepository

    papers = list(VerifiedGeneRepository(tmp_path).iter_papers())

    assert [paper.title for paper in papers] == ["A", "B"]


def test_gene_record_exposes_raw_fields_without_mutating_source():
    from domain import GeneBucket, GeneRecord

    raw = {"Gene_Name": "PSY1", "Species": "Tomato"}
    gene = GeneRecord.from_mapping(bucket=GeneBucket.PATHWAY, data=raw)
    raw["Species"] = "Changed"

    assert gene.name == "PSY1"
    assert gene.field("Species") == "Tomato"
    assert gene.field("Missing", default="NA") == "NA"
