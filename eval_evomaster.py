#!/usr/bin/env python3
"""
Evomaster 评估脚本 - 集成到 NutriBench 评测管线

运行示例：
  # 测试 fs_mv playground
  EVAL_VERSION=v3 EVOMASTER_PLAYGROUND=fs_mv python eval_evomaster.py

  # 测试前 5 道题
  MAX_QUESTIONS=5 python eval_evomaster.py

  # 使用自定义配置
  EVOMASTER_CONFIG=/path/to/config.yaml python eval_evomaster.py
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable

import dotenv

# 加载环境变量
dotenv.load_dotenv(".env.local")
dotenv.load_dotenv()
dotenv.load_dotenv(".eval_env", override=True)

# 添加 Evomaster 到 Python 路径
EVOMASTER_ROOT = Path(os.getenv("EVOMASTER_ROOT", "/data/haotianwu/Evomaster_fs"))
if str(EVOMASTER_ROOT) not in sys.path:
    sys.path.insert(0, str(EVOMASTER_ROOT))

from evomaster_nutribench_adapter import call_evomaster
from notion_client import Client as NotionClient
from openai import AsyncOpenAI


# ===== 配置 =====

QUESTION_DB_ID = os.getenv("QUESTION_DB_ID", "e755b041d920410fa6dd3aa88c421879")
RESULT_DB_ID = os.getenv("RESULT_DB_ID", "c7b1b42c0ac14b5f883725f75860860e")

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.gpugeek.com/v1")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "Vendor2/Gemini-3.1-pro")
EVAL_VERSION = os.getenv("EVAL_VERSION", "v3")
RESULT_WRITE_MODE = os.getenv("RESULT_WRITE_MODE", "append").lower()

# Evomaster 配置
EVOMASTER_PLAYGROUND = os.getenv("EVOMASTER_PLAYGROUND", "fs_mv")
EVOMASTER_CONFIG = os.getenv("EVOMASTER_CONFIG", "")
EVOMASTER_TIMEOUT = int(os.getenv("EVOMASTER_TIMEOUT", "600"))
EVOMASTER_AGENT_NAME = os.getenv("EVOMASTER_AGENT_NAME", f"Evomaster-{EVOMASTER_PLAYGROUND}")

# 评测配置
NUM_RUNS = int(os.getenv("NUM_RUNS", "1"))
MAX_QUESTIONS = int(os.getenv("MAX_QUESTIONS", "0"))
MAX_RUBRICS = int(os.getenv("MAX_RUBRICS", "5"))
AGENT_CONCURRENCY = int(os.getenv("AGENT_CONCURRENCY", "1"))  # Evomaster 建议用 1
JUDGE_CONCURRENCY = int(os.getenv("JUDGE_CONCURRENCY", "3"))
NOTION_CONCURRENCY = int(os.getenv("NOTION_CONCURRENCY", "3"))

NOTION_TEXT_CHUNK = 1800
NOTION_MAX_RICH_TEXT_BLOCKS = 100


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"缺少环境变量 {name}")
    return value


NOTION_API_KEY = require_env("NOTION_API_KEY")
LLM_API_KEY = require_env("LLM_API_KEY")

notion = NotionClient(auth=NOTION_API_KEY)
judge_client = AsyncOpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)


# ===== Notion 读写 =====

def resolve_data_source_id(database_id: str) -> str:
    db = notion.databases.retrieve(database_id=database_id)
    sources = db.get("data_sources") or []
    if not sources:
        raise RuntimeError(f"数据库 {database_id} 没有 data_source")
    return sources[0]["id"]


def fetch_questions() -> list[dict[str, Any]]:
    questions = []
    data_source_id = resolve_data_source_id(QUESTION_DB_ID)
    start_cursor = None

    while True:
        kwargs: dict[str, Any] = {"data_source_id": data_source_id, "page_size": 100}
        if start_cursor:
            kwargs["start_cursor"] = start_cursor

        response = notion.data_sources.query(**kwargs)
        for page in response["results"]:
            question = parse_question(page)
            if question["正文"]:
                questions.append(question)

        if not response.get("has_more"):
            break
        start_cursor = response.get("next_cursor")

    print(f"读取题目: {len(questions)} 道")
    return questions


def parse_question(page: dict[str, Any]) -> dict[str, Any]:
    props = page["properties"]
    rubrics = []

    for i in range(1, MAX_RUBRICS + 1):
        desc = get_text(props, f"采分点{i}-描述")
        score = props.get(f"采分点{i}-分值", {}).get("number")
        if desc:
            rubrics.append({"描述": desc, "满分": float(score or 0)})

    return {
        "page_id": page["id"],
        "编号": props.get("题目编号", {}).get("unique_id", {}).get("number", 0),
        "标题": get_title(props, "题目标题"),
        "正文": get_text(props, "题目正文"),
        "难度": get_select(props, "难度等级"),
        "领域": get_select(props, "领域大类"),
        "小类": get_text(props, "领域小类"),
        "参考答案": get_text(props, "参考答案"),
        "采分点": rubrics,
    }


def write_result(question: dict[str, Any], agent_name: str, run: int, agent_output: str, judge: dict[str, Any]) -> None:
    scores = judge["scores"]
    max_total = sum(r["满分"] for r in question["采分点"])
    total = round(sum(scores), 4)
    rate = round(total / max_total, 4) if max_total else 0

    properties: dict[str, Any] = {
        "Name": title_prop(f"{EVAL_VERSION}|NB-{question['编号']}|{agent_name}|Run{run}"),
        "题目编号": {"number": question["编号"]},
        "题目标题": rich_text_prop(question["标题"]),
        "Agent名称": select_prop(agent_name),
        "运行轮次": select_prop(f"Run{run}"),
        "版本": rich_text_prop(EVAL_VERSION),
        "Agent原始输出": rich_text_prop(agent_output),
        "总分": {"number": total},
        "满分": {"number": max_total},
        "得分率": {"number": rate},
        "评分模型": select_prop(short_model_name(JUDGE_MODEL)),
        "评分原始输出": rich_text_prop(judge["reasoning"]),
    }
    if question["难度"]:
        properties["难度等级"] = select_prop(question["难度"])
    if question["领域"]:
        properties["领域大类"] = select_prop(question["领域"])

    for i, score in enumerate(scores[:MAX_RUBRICS], start=1):
        properties[f"采分点{i}-得分"] = {"number": score}

    if RESULT_WRITE_MODE == "replace":
        existing_page_id = find_existing_result_page(question["编号"], agent_name, run)
        if existing_page_id:
            retry_sync(
                lambda: notion.pages.update(page_id=existing_page_id, properties=properties),
                label="Notion 更新",
            )
            return

    retry_sync(
        lambda: notion.pages.create(parent={"database_id": RESULT_DB_ID}, properties=properties),
        label="Notion 写入",
    )


def find_existing_result_page(question_id: int, agent_name: str, run: int) -> str:
    data_source_id = resolve_data_source_id(RESULT_DB_ID)
    response = retry_sync(
        lambda: notion.data_sources.query(
            data_source_id=data_source_id,
            page_size=1,
            filter={
                "and": [
                    {"property": "题目编号", "number": {"equals": question_id}},
                    {"property": "Agent名称", "select": {"equals": agent_name}},
                    {"property": "运行轮次", "select": {"equals": f"Run{run}"}},
                    {"property": "版本", "rich_text": {"equals": EVAL_VERSION}},
                ]
            },
        ),
        label="Notion 查询旧结果",
    )
    results = response.get("results", [])
    return results[0]["id"] if results else ""


def get_title(props: dict, key: str) -> str:
    field = props.get(key, {})
    items = field.get("title", [])
    return "".join(item.get("plain_text", "") for item in items)


def get_text(props: dict, key: str) -> str:
    field = props.get(key, {})
    items = field.get("rich_text", [])
    return "".join(item.get("plain_text", "") for item in items)


def get_select(props: dict, key: str) -> str:
    field = props.get(key, {})
    select = field.get("select")
    return select.get("name", "") if select else ""


def chunks(text: Any) -> list[dict[str, Any]]:
    value = str(text or "")
    if not value:
        return [{"text": {"content": ""}}]

    pieces = [value[i : i + NOTION_TEXT_CHUNK] for i in range(0, len(value), NOTION_TEXT_CHUNK)]
    if len(pieces) > NOTION_MAX_RICH_TEXT_BLOCKS:
        pieces = pieces[:NOTION_MAX_RICH_TEXT_BLOCKS]
        pieces[-1] = pieces[-1][:1700] + "\n\n[TRUNCATED]"
    pieces = [piece[:2000] for piece in pieces]
    return [{"text": {"content": piece}} for piece in pieces]


def rich_text_prop(text: Any) -> dict[str, Any]:
    return {"rich_text": chunks(text)}


def title_prop(text: str) -> dict[str, Any]:
    return {"title": chunks(str(text)[:NOTION_TEXT_CHUNK])}


def select_prop(name: str) -> dict[str, Any]:
    return {"select": {"name": name}}


def short_model_name(model: str) -> str:
    return {
        "Vendor2/Claude-4.5-Sonnet": "Claude-4.5-Sonnet",
        "Vendor2/GPT-5.4": "GPT-5.4",
        "Vendor2/Gemini-3.1-pro": "Gemini-3.1-pro",
    }.get(model, model.split("/")[-1])


def retry_sync(fn: Callable[[], Any], label: str, attempts: int = 3) -> Any:
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(2 ** (attempt - 1))
    raise RuntimeError(f"{label} 重试 {attempts} 次失败: {last_error}")


async def retry_async(fn: Callable[[], Any], label: str, attempts: int = 3) -> Any:
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return await fn()
        except Exception as exc:
            last_error = exc
            if attempt < attempts:
                await asyncio.sleep(2 ** (attempt - 1))
    raise RuntimeError(f"{label} 重试 {attempts} 次失败: {last_error}")


# ===== Evomaster Agent =====

async def call_evomaster_agent(question_text: str) -> dict[str, Any]:
    """调用 Evomaster agent 回答问题"""
    config_path = EVOMASTER_CONFIG if EVOMASTER_CONFIG else None

    result = await call_evomaster(
        question_text=question_text,
        agent_name=EVOMASTER_PLAYGROUND,
        config_path=config_path,
        timeout=EVOMASTER_TIMEOUT,
    )

    return result


# ===== Judge =====

async def judge_answer(question: dict[str, Any], answer: str) -> dict[str, Any]:
    """使用和 eval_pipeline.py 相同的 LLM 评分标准"""
    prompt = build_judge_prompt(question, answer)

    response = await retry_async(
        lambda: judge_client.chat.completions.create(
            model=JUDGE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=16384,
            temperature=0.1,
        ),
        label="Judge",
    )

    raw = (response.choices[0].message.content or "").strip()
    scores, reasoning = parse_judge_scores(raw, question["采分点"])
    return {"scores": scores, "reasoning": reasoning, "raw": raw}


def build_judge_prompt(question: dict[str, Any], agent_output: str) -> str:
    rubrics = question["采分点"]
    max_total = sum(r["满分"] for r in rubrics)
    rubric_lines = "\n".join(
        f"{i}. ({r['满分']} points) {r['描述']}"
        for i, r in enumerate(rubrics, start=1)
    )
    reference = question.get("参考答案", "")
    ref_section = f"\n***\n\nThe reference answer:\n{reference}\n" if reference else ""

    return f"""You are grading a 植物营养科学 (plant nutrition science) exam answer written in Chinese.

You will be given the problem, a reference answer, a rubric, and the student's attempted answer. The rubric has {len(rubrics)} item(s) and totals up to {max_total} points.

Evaluate the attempted answer against the provided rubric. Pay close attention to detail and grade it strictly, but fairly. Only evaluate against the rubric. Per-item scores can be decimals. Give 0 if the item is not addressed, partial credit if partially addressed, full marks only if fully addressed per the rubric description. If the answer cites non-existent papers, gene IDs, or database entries, deduct on the traceability-related item(s).

***

The problem:
{question["正文"]}
{ref_section}
***

The rubric:
{rubric_lines}

***

The attempted answer:
{agent_output}

***

Explain your reasoning for each rubric item.

Then, on the LAST TWO LINES of your response, output EXACTLY this format and nothing else after them:
SCORES: [<num>, <num>, ...]
VERDICT: <total>"""


def parse_judge_scores(raw: str, rubrics: list[dict[str, Any]]) -> tuple[list[float], str]:
    match = re.search(r"^SCORES\s*:\s*\[([^\]]*)\]\s*$", raw, flags=re.MULTILINE)
    if not match:
        raise ValueError("Judge 输出缺少 SCORES 行")

    numbers = re.findall(r"-?\d+(?:\.\d+)?", match.group(1))
    if len(numbers) != len(rubrics):
        raise ValueError(f"Judge 返回 {len(numbers)} 个分数，期望 {len(rubrics)} 个")

    scores = []
    for number, rubric in zip(numbers, rubrics):
        score = float(number)
        scores.append(min(max(score, 0.0), float(rubric["满分"])))
    return scores, raw[: match.start()].strip()


# ===== 主流程 =====

async def process_one(question: dict[str, Any], run: int, sem_agent: asyncio.Semaphore, sem_judge: asyncio.Semaphore, sem_notion: asyncio.Semaphore) -> dict[str, Any]:
    """处理单个问题"""
    q_id = question["编号"]
    q_title = question["标题"]
    max_score = sum(r["满分"] for r in question["采分点"])

    if not question["采分点"] or max_score <= 0:
        return {
            "question_id": q_id,
            "question_title": q_title,
            "status": "failed",
            "error": "题目缺少有效采分点",
        }

    # 调用 Agent
    async with sem_agent:
        print(f"[Q{q_id}] 调用 {EVOMASTER_AGENT_NAME}...")
        agent_result = await call_evomaster_agent(question["正文"])

    if not agent_result["ok"]:
        print(f"[Q{q_id}] Agent 调用失败: {agent_result['error']}")
        return {
            "question_id": q_id,
            "status": "agent_failed",
            "error": agent_result["error"],
        }

    answer = agent_result["output"]
    print(f"[Q{q_id}] Agent 回答完成 ({len(answer)} 字符)")

    # 评分
    async with sem_judge:
        print(f"[Q{q_id}] 评分中...")
        try:
            judge_result = await judge_answer(question, answer)
        except Exception as exc:
            print(f"[Q{q_id}] Judge 评分失败: {exc}")
            return {
                "question_id": q_id,
                "question_title": q_title,
                "status": "judge_failed",
                "error": str(exc),
            }

    total_score = sum(judge_result["scores"])
    print(f"[Q{q_id}] 得分: {total_score}/{max_score}")

    # 写入 Notion
    async with sem_notion:
        await asyncio.to_thread(
            write_result,
            question,
            EVOMASTER_AGENT_NAME,
            run,
            answer,
            judge_result,
        )

    print(f"[Q{q_id}] 完成")

    return {
        "question_id": q_id,
        "question_title": q_title,
        "status": "success",
        "score": total_score,
        "max_score": max_score,
        "rate": total_score / max_score if max_score else 0,
    }


async def run_evaluation():
    """运行评估"""
    print(f"=== Evomaster 评估 ===")
    print(f"Playground: {EVOMASTER_PLAYGROUND}")
    print(f"Agent 名称: {EVOMASTER_AGENT_NAME}")
    print(f"超时时间: {EVOMASTER_TIMEOUT}s")
    print(f"并发数: Agent={AGENT_CONCURRENCY}, Judge={JUDGE_CONCURRENCY}")
    print()

    # 读取题目
    questions = fetch_questions()
    if MAX_QUESTIONS > 0:
        questions = questions[:MAX_QUESTIONS]

    print(f"将评测 {len(questions)} 道题目，每题运行 {NUM_RUNS} 次")
    print()

    # 创建信号量
    sem_agent = asyncio.Semaphore(AGENT_CONCURRENCY)
    sem_judge = asyncio.Semaphore(JUDGE_CONCURRENCY)
    sem_notion = asyncio.Semaphore(NOTION_CONCURRENCY)

    # 并发处理
    tasks = []
    for run in range(1, NUM_RUNS + 1):
        for question in questions:
            task = process_one(question, run, sem_agent, sem_judge, sem_notion)
            tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 统计结果
    success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
    failed_count = len(results) - success_count

    if success_count > 0:
        total_scores = [r["score"] for r in results if isinstance(r, dict) and r.get("status") == "success"]
        avg_score = sum(total_scores) / len(total_scores)
        print(f"\n=== 评测完成 ===")
        print(f"成功: {success_count}/{len(results)}")
        print(f"失败: {failed_count}/{len(results)}")
        print(f"平均得分: {avg_score:.2f}")
    else:
        print(f"\n=== 评测失败 ===")
        print(f"所有题目均失败")


async def main():
    try:
        await run_evaluation()
    finally:
        await judge_client.close()


if __name__ == "__main__":
    asyncio.run(main())
