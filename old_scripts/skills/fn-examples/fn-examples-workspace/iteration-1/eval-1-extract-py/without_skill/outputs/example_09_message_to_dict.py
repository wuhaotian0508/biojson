"""
example_09_message_to_dict.py

Demonstrates: _message_to_dict(message)

Purpose:
    Converts an OpenAI API message object into a plain Python dict.
    This is useful for logging, saving conversation history, or
    passing messages back into subsequent API calls.

    It extracts:
      - role: always "assistant"
      - content: the text content (or None)
      - tool_calls: list of function call dicts (if any)

    Since OpenAI message objects are not plain dicts, this function
    bridges the gap for serialization.
"""

import json


def _message_to_dict(message) -> dict:
    """Convert an OpenAI message object to dict."""
    msg = {"role": "assistant", "content": message.content or None}
    if message.tool_calls:
        msg["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in message.tool_calls
        ]
    return msg


# ── We simulate OpenAI message objects with simple classes ────────────────

class FakeFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class FakeToolCall:
    def __init__(self, id, function):
        self.id = id
        self.function = function


class FakeMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


# ── Example 1: Message with text content only ────────────────────────────

print("=== Example 1: Text-only message ===")
msg1 = FakeMessage(content="I found 3 genes in this paper.", tool_calls=None)
result1 = _message_to_dict(msg1)
print(json.dumps(result1, indent=2))

# ── Example 2: Message with tool calls (function calling) ────────────────

print("\n=== Example 2: Message with tool calls ===")
msg2 = FakeMessage(
    content=None,
    tool_calls=[
        FakeToolCall(
            id="call_abc123",
            function=FakeFunction(
                name="extract_all_genes",
                arguments='{"Title": "Test Paper", "DOI": "10.1234/test", "Common_Genes": []}'
            )
        )
    ]
)
result2 = _message_to_dict(msg2)
print(json.dumps(result2, indent=2))

# ── Example 3: Message with multiple tool calls ──────────────────────────

print("\n=== Example 3: Multiple tool calls ===")
msg3 = FakeMessage(
    content="Analyzing the paper...",
    tool_calls=[
        FakeToolCall(
            id="call_001",
            function=FakeFunction("extract_common_genes", '{"genes": []}')
        ),
        FakeToolCall(
            id="call_002",
            function=FakeFunction("extract_pathway_genes", '{"genes": [{"Gene_Name": "CHS"}]}')
        ),
    ]
)
result3 = _message_to_dict(msg3)
print(json.dumps(result3, indent=2))
