from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


DATASET_SCHEMA_VERSION = "dataset_export.v1"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def load_capture_dir(input_dir: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    interactions = [
        row
        for row in read_jsonl(input_dir / "interactions.jsonl")
        if row.get("record_type") == "interaction"
    ]
    feedback_rows = [
        row
        for row in read_jsonl(input_dir / "feedback.jsonl")
        if row.get("record_type") == "feedback"
    ]
    feedback_by_interaction: dict[str, dict[str, Any]] = {}
    for row in feedback_rows:
        interaction_id = row.get("interaction_id")
        if interaction_id:
            feedback_by_interaction[interaction_id] = row
    return interactions, feedback_by_interaction


def sft_rows(
    interactions: list[dict[str, Any]],
    feedback_by_interaction: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for record in interactions:
        final = record.get("final") or {}
        answer = final.get("answer_text") or ""
        messages = list(record.get("messages") or [])
        if record.get("status") != "completed" or not answer or not messages:
            continue
        messages.append({"role": "assistant", "content": answer})
        interaction_id = record.get("interaction_id", "")
        feedback = feedback_by_interaction.get(interaction_id)
        rows.append(
            {
                "schema_version": DATASET_SCHEMA_VERSION,
                "task": "sft",
                "id": interaction_id,
                "source": "production",
                "messages": messages,
                "metadata": {
                    "session_id": record.get("session_id", ""),
                    "turn_id": record.get("turn_id", ""),
                    "created_at": record.get("created_at", ""),
                    "model_id": (record.get("request") or {}).get("model_id", ""),
                    "use_personal": (record.get("request") or {}).get("use_personal", False),
                    "use_depth": (record.get("request") or {}).get("use_depth", False),
                    "tools_used": final.get("tools_used", []),
                    "citations": final.get("citations", []),
                    "feedback": feedback.get("rating") if feedback else "",
                },
            }
        )
    return rows


def preference_rows(
    interactions: list[dict[str, Any]],
    feedback_by_interaction: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: {"up": [], "down": []})
    for record in interactions:
        final = record.get("final") or {}
        answer = final.get("answer_text") or ""
        feedback = feedback_by_interaction.get(record.get("interaction_id", ""))
        if record.get("status") != "completed" or not answer or not feedback:
            continue
        rating = feedback.get("rating")
        if rating not in {"up", "down"}:
            continue
        query = ((record.get("request") or {}).get("query") or "").strip().lower()
        if not query:
            continue
        grouped[query][rating].append(record)

    rows = []
    for query, bucket in grouped.items():
        for chosen in bucket["up"]:
            for rejected in bucket["down"]:
                rows.append(
                    {
                        "schema_version": DATASET_SCHEMA_VERSION,
                        "task": "preference",
                        "id": f"{chosen.get('interaction_id')}__vs__{rejected.get('interaction_id')}",
                        "source": "production_feedback",
                        "prompt": chosen.get("messages") or [],
                        "chosen": (chosen.get("final") or {}).get("answer_text", ""),
                        "rejected": (rejected.get("final") or {}).get("answer_text", ""),
                        "metadata": {
                            "query": query,
                            "chosen_interaction_id": chosen.get("interaction_id", ""),
                            "rejected_interaction_id": rejected.get("interaction_id", ""),
                        },
                    }
                )
    return rows


def raw_rows(
    interactions: list[dict[str, Any]],
    feedback_by_interaction: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for record in interactions:
        next_record = dict(record)
        feedback = feedback_by_interaction.get(record.get("interaction_id", ""))
        if feedback:
            next_record["feedback"] = feedback
        rows.append(next_record)
    return rows


def build_rows(
    export_format: str,
    interactions: list[dict[str, Any]],
    feedback_by_interaction: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    if export_format == "sft":
        return sft_rows(interactions, feedback_by_interaction)
    if export_format == "preference":
        return preference_rows(interactions, feedback_by_interaction)
    if export_format == "raw":
        return raw_rows(interactions, feedback_by_interaction)
    raise ValueError(f"Unsupported format: {export_format}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export NutriMaster interaction captures into training datasets.")
    parser.add_argument("--input-dir", type=Path, default=Path("data/interactions"))
    parser.add_argument("--output", type=Path, default=Path("data/interactions/dataset_sft.jsonl"))
    parser.add_argument("--format", choices=["sft", "preference", "raw"], default="sft")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    interactions, feedback_by_interaction = load_capture_dir(args.input_dir)
    rows = build_rows(args.format, interactions, feedback_by_interaction)
    count = write_jsonl(args.output, rows)
    print(f"Exported {count} {args.format} rows to {args.output}")


if __name__ == "__main__":
    main()
