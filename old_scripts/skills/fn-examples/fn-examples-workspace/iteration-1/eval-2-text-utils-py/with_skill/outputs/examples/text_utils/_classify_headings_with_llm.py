"""
_classify_headings_with_llm — Call an LLM API to decide which paper section
headings should be removed (e.g., Introduction, References, Acknowledgments).

Source: extractor/text_utils.py:201

NOTE: This example uses a mock OpenAI client instead of making real API calls.
The mock returns a realistic response so the function's parsing logic runs
end-to-end.

Usage:
    python _classify_headings_with_llm.py
"""

# --- External Imports ---
import re
import os
import json
from unittest.mock import MagicMock, patch


# --- Target Function ---

def _classify_headings_with_llm(headings):
    """
    调用 LLM API 判断哪些标题需要被去除（反向逻辑）。

    Args:
        headings: list of str，论文中所有 '# ' 标题

    Returns:
        set of int，需要去除的标题索引（0-based）
    """
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
    )
    model = os.getenv("MODEL", "Vendor2/Claude-4.6-opus")

    # 构建标题编号列表
    heading_list = "\n".join(f"{i}: {h}" for i, h in enumerate(headings))

    prompt = f"""Below is a numbered list of section headings from a scientific paper.
Please identify which headings should be REMOVED because they are NOT relevant to experimental results or methods.

Remove these types of sections:
- Introduction / Background
- References / References and Notes / Literature Cited
- Acknowledgments / Acknowledgements
- Author Contributions / Authors Contributions
- Funding / Financial Support
- Competing Interests / Conflict of Interest
- Additional Information
- Resource Distribution

Keep everything else (including Results, Methods, Discussion, paper title sections with content, Supplementary Materials, Accession Numbers etc.)

Headings:
{heading_list}

Return ONLY a JSON array of the index numbers that should be REMOVED.
Example: [0, 2, 4]
If nothing should be removed, return: []"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that identifies irrelevant sections in scientific papers. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=200,
        )
        answer = response.choices[0].message.content.strip()

        # 提取 JSON 数组
        json_match = re.search(r'\[[\d\s,]*\]', answer)
        if json_match:
            indices = json.loads(json_match.group())
            return set(int(i) for i in indices if 0 <= i < len(headings))
        else:
            print(f"    [text_utils] LLM returned unparseable result: {answer}")
            return None

    except Exception as e:
        print(f"    [text_utils] LLM section classification call failed: {e}")
        return None


# --- Mock Setup ---
# We mock the OpenAI client so this example runs without real API credentials.
# The mock simulates a realistic LLM response: given 6 headings, it returns
# indices [1, 4, 5] indicating that Introduction, References, and
# Acknowledgments should be removed.

def _create_mock_response(removed_indices):
    """Build a mock OpenAI ChatCompletion response object."""
    mock_message = MagicMock()
    mock_message.content = json.dumps(removed_indices)

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


# --- Sample Input ---
# Typical headings from a plant molecular biology paper.
# Indices 1 (Introduction), 4 (References), and 5 (Acknowledgments) should
# be flagged for removal by the LLM.

sample_headings = [
    "# Enrichment of Tomato Fruit with Anthocyanins",   # 0 - keep (title)
    "# Introduction",                                     # 1 - remove
    "# Results",                                          # 2 - keep
    "# Materials and Methods",                            # 3 - keep
    "# References",                                       # 4 - remove
    "# Acknowledgments",                                  # 5 - remove
]


# --- Run ---
if __name__ == "__main__":
    # The indices the mock LLM will say to remove
    expected_removed = [1, 4, 5]

    mock_response = _create_mock_response(expected_removed)

    # Patch OpenAI client so no real API call is made
    with patch("openai.OpenAI") as MockOpenAI:
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        MockOpenAI.return_value = mock_client_instance

        # Also set dummy env vars so load_dotenv doesn't cause issues
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-mock-key-for-testing",
            "OPENAI_BASE_URL": "https://mock.api.example.com/v1",
            "MODEL": "mock-model",
        }):
            result = _classify_headings_with_llm(sample_headings)

    print("=== Input Headings ===")
    for i, h in enumerate(sample_headings):
        print(f"  [{i}] {h}")

    print()
    print(f"=== Indices to Remove (from mock LLM) ===")
    print(f"  {result}")

    print()
    print("=== Interpretation ===")
    for i, h in enumerate(sample_headings):
        status = "REMOVE" if i in result else "KEEP"
        print(f"  [{i}] {status:6s}  {h}")
