from __future__ import annotations

from pathlib import Path


def test_obsolete_legacy_rag_modules_are_removed():
    root = Path(__file__).resolve().parents[2]
    assert not (root / "api").exists()
    assert not (root / "admin").exists()
    assert not (root / "rag").exists()

    obsolete = [
        "backup/generation/__init__.py",
        "backup/generation/generator.py",
        "backup/ragtry/README.md",
        "backup/ragtry/PLAN.md",
        "backup/ragtry/build_site.py",
        "backup/ragtry/config.py",
        "backup/ragtry/data_loader.py",
        "backup/ragtry/generator.py",
        "backup/ragtry/main.py",
        "backup/ragtry/retriever.py",
        "backup/ragtry/site/index.html",
        "backup/ragtry/translate.json",
        "backup/ragtry/web/app.py",
        "backup/ragtry/web/requirements.txt",
        "backup/ragtry/web/run.sh",
        "backup/ragtry/web/run_prod.sh",
        "backup/ragtry/web/static/app.js",
        "backup/ragtry/web/static/index.html",
        "backup/ragtry/web/static/style.css",
        "rag/utils/__init__.py",
        "rag/utils/simple_retriever.py",
        "rag/utils/build_index.py",
        "rag/utils/chunker/base.py",
        "rag/utils/chunker/field_formatter.py",
        "rag/utils/chunker/generic.py",
        "rag/utils/chunker/mixed_bucket.py",
        "rag/utils/chunker/pathway_chain.py",
        "rag/utils/chunker/plant_genes.py",
        "rag/utils/chunker/router.py",
        "rag/utils/chunker/schemas.py",
        "rag/search/query_expander.py",
        "rag/search/bm25_retriever.py",
        "rag/scripts/smoke_test_hybrid.py",
        "rag/scripts/rebuild_index.py",
        "rag/scripts/build_bm25_index.py",
        "rag/test_imports.py",
        "rag/test_pubmed_optimizer.py",
        "rag/test_query_translator.py",
        "rag/test_rag_search.py",
        "rag/_inspect_game8.py",
    ]

    assert [path for path in obsolete if (root / path).exists()] == []
