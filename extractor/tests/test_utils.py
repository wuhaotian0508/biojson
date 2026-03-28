"""
Tests for extractor/utils.py shared utilities.

Run: python -m pytest extractor/tests/test_utils.py -v
"""

from extractor.utils import ensure_list, get_gene_name, safe_parse_json, stem_to_dirname


# ═══════════════════════════════════════════════════════════════════════════════
#  ensure_list
# ═══════════════════════════════════════════════════════════════════════════════

class TestEnsureList:

    def test_already_list(self):
        assert ensure_list([1, 2, 3]) == [1, 2, 3]

    def test_empty_list(self):
        assert ensure_list([]) == []

    def test_json_string(self):
        assert ensure_list('[1, 2]') == [1, 2]

    def test_invalid_json_string(self):
        assert ensure_list('not json') == []

    def test_json_string_not_list(self):
        assert ensure_list('{"a": 1}') == []

    def test_none(self):
        assert ensure_list(None) == []

    def test_int(self):
        assert ensure_list(42) == []


# ═══════════════════════════════════════════════════════════════════════════════
#  get_gene_name
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetGeneName:

    def test_gene_name_key(self):
        assert get_gene_name({"Gene_Name": "TaGS5"}) == "TaGS5"

    def test_gene_key(self):
        assert get_gene_name({"gene": "BIK1"}) == "BIK1"

    def test_gene_name_lowercase(self):
        assert get_gene_name({"gene_name": "Pi2"}) == "Pi2"

    def test_name_key(self):
        assert get_gene_name({"name": "LOX3"}) == "LOX3"

    def test_priority_order(self):
        assert get_gene_name({"Gene_Name": "A", "gene": "B"}) == "A"

    def test_empty_dict(self):
        assert get_gene_name({}) == ""

    def test_empty_gene_name_falls_through(self):
        assert get_gene_name({"Gene_Name": "", "gene": "fallback"}) == "fallback"


# ═══════════════════════════════════════════════════════════════════════════════
#  safe_parse_json
# ═══════════════════════════════════════════════════════════════════════════════

class TestSafeParseJson:

    def test_valid_json(self):
        assert safe_parse_json('{"a": 1}') == {"a": 1}

    def test_truncated_json_repair(self):
        # Needs at least one '}' to attempt repair
        result = safe_parse_json('{"a": [1, 2]}extra', "test")
        assert result is not None
        assert result["a"] == [1, 2]

    def test_completely_invalid(self):
        assert safe_parse_json('not json at all') is None

    def test_empty_string(self):
        assert safe_parse_json('') is None


# ═══════════════════════════════════════════════════════════════════════════════
#  stem_to_dirname
# ═══════════════════════════════════════════════════════════════════════════════

class TestStemToDirname:

    def test_basic(self):
        assert stem_to_dirname("my_paper_name") == "my-paper-name"

    def test_mineru_prefix(self):
        assert stem_to_dirname("MinerU_markdown_my_paper") == "my-paper"

    def test_duplicate_suffix(self):
        # _(1) is removed, then _ replaced with -
        assert stem_to_dirname("my_paper_(1)") == "my-paper"

    def test_combined(self):
        assert stem_to_dirname("MinerU_markdown_cool_paper_(1)") == "cool-paper"
