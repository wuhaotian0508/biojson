import os

import pytest
import requests
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

REQUIRED_REAL_SERVICE_ENV = [
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "MODEL",
    "JINA_API_KEY",
]


def _require_env(keys: list[str]) -> dict[str, str]:
    missing = [key for key in keys if not os.getenv(key)]
    assert not missing, f"Missing required real-service env vars: {', '.join(missing)}"
    return {key: os.environ[key] for key in keys}


@pytest.mark.integration
def test_real_llm_chat_completion_returns_text():
    env = _require_env(["OPENAI_API_KEY", "OPENAI_BASE_URL", "MODEL"])
    client = OpenAI(
        api_key=env["OPENAI_API_KEY"],
        base_url=env["OPENAI_BASE_URL"],
    )

    response = client.chat.completions.create(
        model=env["MODEL"],
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: nutrimaster-ok",
            }
        ],
        temperature=0,
        max_tokens=16,
    )

    content = response.choices[0].message.content or ""
    assert "nutrimaster-ok" in content.lower()


@pytest.mark.integration
def test_real_jina_embedding_returns_vector():
    env = _require_env(["JINA_API_KEY"])

    response = requests.post(
        "https://api.jina.ai/v1/embeddings",
        headers={
            "Authorization": f"Bearer {env['JINA_API_KEY']}",
            "Content-Type": "application/json",
        },
        json={
            "model": "jina-embeddings-v3",
            "input": ["NutriMaster validates plant nutrition gene retrieval."],
            "task": "retrieval.passage",
        },
        timeout=60,
    )

    assert response.status_code == 200, response.text[:500]
    vector = response.json()["data"][0]["embedding"]
    assert isinstance(vector, list)
    assert len(vector) > 100


@pytest.mark.integration
def test_real_pubmed_search_is_reachable():
    try:
        response = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={
                "db": "pubmed",
                "term": "tomato lycopene biosynthesis",
                "retmode": "json",
                "retmax": "1",
            },
            timeout=30,
        )
    except requests.RequestException as exc:
        pytest.fail(f"PubMed real-service request failed: {exc}")

    assert response.status_code == 200, response.text[:500]
    payload = response.json()
    assert payload["esearchresult"]["count"].isdigit()
