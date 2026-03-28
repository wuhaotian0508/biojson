"""
_message_to_dict — Convert an OpenAI chat completion message object to a plain dict.

Extracts role, content, and tool_calls (if any) from the API response message
into a serializable dictionary format.

Source: extractor/extract.py:317

Usage:
    python _message_to_dict.py
"""

import json

# --- Mock OpenAI message objects ---
# We create lightweight mock objects that mimic the structure of
# openai.types.chat.ChatCompletionMessage and its nested types.

class MockFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments

class MockToolCall:
    def __init__(self, id, function_name, arguments):
        self.id = id
        self.type = "function"
        self.function = MockFunction(function_name, arguments)

class MockMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.role = "assistant"
        self.tool_calls = tool_calls

# --- Target Function ---

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

# --- Sample Input ---

# Case 1: Message with tool calls (typical extract_all_genes response)
tool_call_args = json.dumps({
    "Title": "Flavonoid biosynthesis in tomato",
    "Journal": "Nature Communications",
    "DOI": "10.1038/s41467-015-3298-7",
    "Common_Genes": [],
    "Pathway_Genes": [{"Gene_Name": "SlCHI1", "Species": "tomato"}],
    "Regulation_Genes": [{"Gene_Name": "SlMYB12", "Species": "tomato"}],
})

message_with_tools = MockMessage(
    content=None,
    tool_calls=[
        MockToolCall(
            id="call_abc123",
            function_name="extract_all_genes",
            arguments=tool_call_args,
        )
    ],
)

# Case 2: Message with plain text content (no tool calls)
message_plain = MockMessage(
    content="I found 3 genes related to flavonoid metabolism in this paper.",
    tool_calls=None,
)

# --- Run ---
if __name__ == "__main__":
    print("=== Case 1: Message with tool calls ===")
    result1 = _message_to_dict(message_with_tools)
    print(json.dumps(result1, indent=2, ensure_ascii=False))

    print("\n=== Case 2: Plain text message ===")
    result2 = _message_to_dict(message_plain)
    print(json.dumps(result2, indent=2, ensure_ascii=False))
