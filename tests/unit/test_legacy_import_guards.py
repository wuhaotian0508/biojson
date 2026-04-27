from pathlib import Path


def test_legacy_llm_client_bridge_has_been_removed():
    root = Path(__file__).resolve().parents[2]

    assert not (root / "rag" / "core" / "llm_client.py").exists()
