"""
Tests for verify.py report-building and statistics.

Run: python -m pytest extractor/tests/test_verify_report.py -v
"""

from pathlib import Path

from extractor.verify import _build_verification_report, _apply_corrections


class TestBuildVerificationReport:
    """Regression tests for stats/summary counting in _build_verification_report."""

    def _make_report(self, verdicts_by_gene):
        """Helper: build a report from a dict of {gene_name: [field_verdicts]}."""
        extraction_dict = {
            "Title": "Test", "Journal": "J", "DOI": "10/x",
            "Common_Genes": [],
            "Pathway_Genes": [],
            "Regulation_Genes": [],
        }
        all_genes_with_info = []
        all_gene_verdicts = []

        for i, (gname, fvs) in enumerate(verdicts_by_gene.items()):
            gene_data = {"Gene_Name": gname, "Species": "rice"}
            extraction_dict["Common_Genes"].append(gene_data)
            all_genes_with_info.append((gene_data, "Common", "Common_Genes", i))
            all_gene_verdicts.append({
                "Gene_Name": gname,
                "field_verdicts": fvs,
            })

        report, _ = _build_verification_report(
            extraction_dict, all_genes_with_info, all_gene_verdicts,
            "test_stem", Path("/tmp/fake.md"),
        )
        return report

    def test_single_supported_verdict(self):
        report = self._make_report({
            "GeneA": [
                {"field_name": "Species", "verdict": "SUPPORTED", "reason": "ok"},
            ],
        })

        gene_stats = report["genes"][0]["stats"]
        assert gene_stats["supported"] == 1
        assert gene_stats["unsupported"] == 0
        assert gene_stats["uncertain"] == 0

        s = report["summary"]
        assert s["total_fields"] == 1
        assert s["supported"] == 1

    def test_mixed_verdicts(self):
        report = self._make_report({
            "GeneA": [
                {"field_name": "Species", "verdict": "SUPPORTED", "reason": "ok"},
                {"field_name": "Trait", "verdict": "UNSUPPORTED", "reason": "not found"},
                {"field_name": "Function", "verdict": "UNCERTAIN", "reason": "partial"},
            ],
        })

        gene_stats = report["genes"][0]["stats"]
        assert gene_stats["supported"] == 1
        assert gene_stats["unsupported"] == 1
        assert gene_stats["uncertain"] == 1

        s = report["summary"]
        assert s["total_fields"] == 3
        assert s["supported"] == 1
        assert s["unsupported"] == 1
        assert s["uncertain"] == 1
        assert s["total_corrections"] == 1  # UNSUPPORTED → NA

    def test_multi_gene_summary_aggregation(self):
        report = self._make_report({
            "GeneA": [
                {"field_name": "Species", "verdict": "SUPPORTED", "reason": "ok"},
            ],
            "GeneB": [
                {"field_name": "Species", "verdict": "UNSUPPORTED", "reason": "bad"},
                {"field_name": "Trait", "verdict": "SUPPORTED", "reason": "ok"},
            ],
        })

        s = report["summary"]
        assert s["total_fields"] == 3
        assert s["supported"] == 2
        assert s["unsupported"] == 1
        assert s["total_corrections"] == 1

    def test_empty_verdicts(self):
        report = self._make_report({"GeneA": []})

        gene_stats = report["genes"][0]["stats"]
        assert gene_stats == {"supported": 0, "unsupported": 0, "uncertain": 0}
        assert report["summary"]["total_fields"] == 0

    def test_lowercase_verdict_still_counted(self):
        """Verdicts may come back in varying case from the API."""
        report = self._make_report({
            "GeneA": [
                {"field_name": "Species", "verdict": "supported", "reason": "ok"},
                {"field_name": "Trait", "verdict": "Unsupported", "reason": "no"},
            ],
        })

        gene_stats = report["genes"][0]["stats"]
        assert gene_stats["supported"] == 1
        assert gene_stats["unsupported"] == 1


class TestApplyCorrections:

    def test_unsupported_corrected_to_na(self):
        gene = {"Gene_Name": "X", "Species": "rice", "Trait": "yield"}
        corrected, corrections = _apply_corrections(gene, [
            {"field_name": "Trait", "verdict": "UNSUPPORTED", "reason": "not found"},
        ])

        assert corrected["Trait"] == "NA"
        assert corrected["Species"] == "rice"  # untouched
        assert len(corrections) == 1
        assert corrections[0]["field"] == "Trait"

    def test_supported_not_corrected(self):
        gene = {"Gene_Name": "X", "Species": "rice"}
        corrected, corrections = _apply_corrections(gene, [
            {"field_name": "Species", "verdict": "SUPPORTED", "reason": "ok"},
        ])

        assert corrected["Species"] == "rice"
        assert corrections == []
