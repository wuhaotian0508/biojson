from __future__ import annotations

import json
import logging
import re

from nutrimaster.agent.prompts import PromptBuilder
from nutrimaster.experiment import extract_gene_names
from nutrimaster.rag.evidence import CitationRegistry, EvidencePacket, evidence_key

logger = logging.getLogger(__name__)

MAX_STEPS = 12


class Agent:
    """Small LLM tool loop over high-level NutriMaster tools."""

    def __init__(self, registry, skill_loader, call_llm, prompt_builder: PromptBuilder | None = None):
        self.registry = registry
        self.loader = skill_loader
        self.call_llm = call_llm
        self.prompt_builder = prompt_builder or PromptBuilder(skill_loader)

    @staticmethod
    def _msg_to_dict(msg, model_id: str = "") -> dict:
        if hasattr(msg, "model_dump"):
            data = msg.model_dump(exclude_none=True)
        elif isinstance(msg, dict):
            data = dict(msg)
        else:
            data = {
                key: getattr(msg, key)
                for key in ("role", "content", "tool_calls", "reasoning_content")
                if hasattr(msg, key) and getattr(msg, key) is not None
            }
        data.setdefault("role", "assistant")
        return data

    @staticmethod
    def _truncate_history(history: list, max_chars_per_msg: int = 800) -> list:
        truncated = []
        for msg in history or []:
            content = msg.get("content", "")
            if msg.get("role") == "assistant" and isinstance(content, str) and len(content) > max_chars_per_msg:
                truncated.append({**msg, "content": content[:max_chars_per_msg] + "\n...(之前回答已截断)"})
            else:
                truncated.append(msg)
        return truncated

    @staticmethod
    def _strip_reasoning_for_new_turn(messages: list[dict]) -> list[dict]:
        output = []
        for msg in messages:
            if msg.get("role") == "assistant" and "reasoning_content" in msg:
                output.append({key: value for key, value in msg.items() if key != "reasoning_content"})
            else:
                output.append(msg)
        return output

    @staticmethod
    def _filter_citations(answer_text: str, evidence_packets: list[EvidencePacket]) -> list[dict]:
        citations = Agent._unique_citations(
            citation
            for packet in evidence_packets
            for citation in packet.citations
        )
        if not citations:
            return []
        cited_numbers = {
            int(match.group(1))
            for match in re.finditer(r"\[(\d+)\]", answer_text or "")
        }
        if not cited_numbers:
            return citations
        filtered = [
            citation
            for citation in citations
            if citation.get("tool_index") in cited_numbers
        ]
        return filtered or citations

    @staticmethod
    def _unique_citations(citations) -> list[dict]:
        output = []
        seen: set[tuple[str, str]] = set()
        for citation in citations:
            key = evidence_key(
                title=citation.get("title", ""),
                doi=citation.get("doi", ""),
                pmid=citation.get("pmid", ""),
                url=citation.get("url", ""),
            )
            if key == ("title", ""):
                key = ("source_id", str(citation.get("tool_index") or citation.get("source_id") or len(output) + 1))
            if key in seen:
                continue
            seen.add(key)
            output.append(citation)
        return output

    @staticmethod
    def _get_value(obj, key: str, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    async def run(
        self,
        user_input: str,
        user_id: str | None = None,
        model_id: str = "",
        history: list | None = None,
        use_personal: bool = False,
        use_depth: bool = False,
        skill_prefs: dict | None = None,
        tool_overrides: dict | None = None,
    ):
        try:
            yield {"type": "tools_enabled", "tools": sorted(self.registry.tool_names)}
            messages = [
                {
                    "role": "system",
                    "content": self.prompt_builder.build(
                        user_id=user_id,
                        use_depth=use_depth,
                        use_personal=use_personal,
                    ),
                }
            ]
            messages.extend(self._truncate_history(history or []))
            messages.append({"role": "user", "content": user_input})
            messages = self._strip_reasoning_for_new_turn(messages)

            citation_registry = CitationRegistry()
            evidence_packets: list[EvidencePacket] = []
            answer_text = ""
            for _step in range(MAX_STEPS):
                response = await self.call_llm(
                    messages,
                    tools=self.registry.get_definitions,
                    model_id=model_id,
                    is_agent_call=True,
                )
                assistant_message = self._msg_to_dict(response, model_id=model_id)
                messages.append(assistant_message)

                tool_calls = getattr(response, "tool_calls", None) or assistant_message.get("tool_calls") or []
                if not tool_calls:
                    answer_text = response.content if hasattr(response, "content") else assistant_message.get("content", "")
                    break

                for tool_call in tool_calls:
                    function = self._get_value(tool_call, "function", {})
                    tool_name = self._get_value(function, "name")
                    raw_args = self._get_value(function, "arguments", "{}") or "{}"
                    args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
                    if tool_name == "rag_search":
                        args.setdefault("include_personal", use_personal)
                        args.setdefault("mode", "deep" if use_depth else "normal")
                    if user_id:
                        args.setdefault("user_id", user_id)
                    yield {"type": "tool_call", "tool": tool_name, "args": args}
                    try:
                        result = await self.registry.execute(tool_name, **args)
                    except Exception as exc:
                        result = f"工具执行失败: {exc}"
                    if isinstance(result, EvidencePacket):
                        global_packet = citation_registry.assign_packet(result)
                        evidence_packets.append(global_packet)
                        tool_content = global_packet.to_tool_text()
                    elif hasattr(result, "to_tool_text"):
                        tool_content = result.to_tool_text()
                    else:
                        tool_content = str(result)
                    yield {
                        "type": "tool_result",
                        "tool": tool_name,
                        "summary": tool_content[:500],
                        "content": tool_content,
                    }
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": self._get_value(tool_call, "id", tool_name),
                            "name": tool_name,
                            "content": tool_content,
                        }
                    )

            if answer_text:
                yield {"type": "text", "data": answer_text}
            citations = self._filter_citations(answer_text, evidence_packets)
            if citations:
                yield {"type": "citations", "data": citations}
                yield {"type": "sources", "data": citations}
            genes = extract_gene_names(answer_text or user_input)
            if genes:
                yield {"type": "genes_available", "genes": genes}
            yield {"type": "done"}
        except Exception as exc:
            logger.exception("Agent run failed")
            yield {"type": "error", "data": str(exc)}


__all__ = ["Agent"]
